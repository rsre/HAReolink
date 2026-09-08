const CARD_VERSION = "0.4.1";

class ReolinkWebCameraCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._config = undefined;
    this._peer = undefined;
    this._remoteStream = undefined;
    this._micStream = undefined;
    this._audioSender = undefined;
    this._sessionId = undefined;
    this._pendingCandidates = [];
    this._unsubscribe = undefined;
    this._starting = false;
    this._talking = false;
    this._talkRequested = false;
    this._muted = true;
    this._mutedBeforeTalk = undefined;
  }

  static getStubConfig(hass, entities) {
    const entity = entities?.find((candidate) => candidate.startsWith("camera."));
    return { entity: entity || "" };
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "entity", required: true, selector: { entity: { domain: "camera" } } },
        { name: "title", selector: { text: {} } },
        { name: "hide_title", selector: { boolean: {} } },
      ],
      computeLabel: (schema) => ({
        entity: "Camera entity",
        title: "Title",
        hide_title: "Hide card title",
      })[schema.name],
    };
  }

  setConfig(config) {
    if (!config.entity || !config.entity.startsWith("camera.")) {
      throw new Error("A camera entity is required");
    }
    const previous = this._config;
    const changed = previous?.entity !== config.entity;
    this._config = {
      hide_title: false,
      ...config,
    };
    if (!previous || changed) this._muted = true;
    this._render();
    if (changed && this.isConnected) {
      this._restart();
    }
  }

  set hass(hass) {
    const firstUpdate = !this._hass;
    this._hass = hass;
    if (firstUpdate && this.isConnected) {
      this._start();
    }
    this._updateTitle();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return { rows: 5, columns: 12, min_rows: 3, min_columns: 6 };
  }

  connectedCallback() {
    this._render();
    this._start();
    document.addEventListener("visibilitychange", this._visibilityHandler);
  }

  disconnectedCallback() {
    document.removeEventListener("visibilitychange", this._visibilityHandler);
    this._cleanup();
  }

  _visibilityHandler = () => {
    if (document.hidden) {
      this._cleanup();
    } else {
      this._start();
    }
  };

  _render() {
    if (!this.shadowRoot || !this._config) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; background: var(--ha-card-background, var(--card-background-color)); }
        .header { padding: 12px 16px; font-size: 16px; font-weight: 500; }
        .stage { position: relative; background: #000; aspect-ratio: 16 / 9; cursor: pointer; }
        video { width: 100%; height: 100%; display: block; object-fit: contain; background: #000; }
        .status { position: absolute; inset: auto 10px 10px; padding: 6px 9px; border-radius: 6px;
          color: white; background: rgba(0,0,0,.68); font-size: 12px; pointer-events: none; }
        .status:empty { display: none; }
        .controls { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 12px; }
        button { border: 0; border-radius: 999px; min-width: 44px; height: 44px; padding: 0 14px;
          background: var(--secondary-background-color); color: var(--primary-text-color); cursor: pointer;
          touch-action: none; user-select: none; font: inherit; }
        button:hover { filter: brightness(1.08); }
        button:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
        .talk { min-width: 132px; background: var(--primary-color); color: var(--text-primary-color, white); }
        .talk.active { background: var(--error-color, #db4437); transform: scale(.97); }
        .talk:disabled { opacity: .55; cursor: wait; }
      </style>
      <ha-card>
        ${this._config.hide_title ? "" : '<div class="header"></div>'}
        <div class="stage" role="button" tabindex="0" aria-label="Open camera stream">
          <video autoplay playsinline muted></video>
          <div class="status">Connecting…</div>
        </div>
        <div class="controls">
          <button class="sound" type="button" title="Enable camera audio" aria-label="Enable camera audio">🔇</button>
          <button class="talk" type="button" aria-label="Hold to talk">Hold to talk</button>
        </div>
      </ha-card>`;

    this._video = this.shadowRoot.querySelector("video");
    this._video.muted = this._muted;
    this._status = this.shadowRoot.querySelector(".status");
    this._talkButton = this.shadowRoot.querySelector(".talk");
    this._soundButton = this.shadowRoot.querySelector(".sound");

    this._talkButton.addEventListener("pointerdown", this._beginTalk);
    this._talkButton.addEventListener("pointerup", this._endTalk);
    this._talkButton.addEventListener("pointercancel", this._endTalk);
    this._talkButton.addEventListener("pointerleave", this._endTalk);
    this._talkButton.addEventListener("keydown", this._talkKeyDown);
    this._talkButton.addEventListener("keyup", this._talkKeyUp);
    this._soundButton.addEventListener("click", this._toggleSound);
    const stage = this.shadowRoot.querySelector(".stage");
    stage.addEventListener("click", this._openMoreInfo);
    stage.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") this._openMoreInfo(event);
    });
    this._updateTitle();
    this._updateSoundButton();
  }

  _updateTitle() {
    const header = this.shadowRoot?.querySelector(".header");
    if (!header || !this._config) return;
    const state = this._hass?.states?.[this._config.entity];
    header.textContent = this._config.title || state?.attributes?.friendly_name || this._config.entity;
  }

  _setStatus(message) {
    if (this._status) this._status.textContent = message || "";
  }

  _openMoreInfo = (event) => {
    event.preventDefault();
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      bubbles: true,
      composed: true,
      detail: { entityId: this._config.entity },
    }));
  };

  async _restart() {
    await this._cleanup();
    await this._start();
  }

  async _start() {
    if (this._starting || this._peer || !this._hass || !this._config || document.hidden) return;
    this._starting = true;
    this._setStatus("Connecting…");
    try {
      if (!window.RTCPeerConnection) throw new Error("This browser does not support WebRTC");
      const clientConfig = await this._hass.callWS({
        type: "camera/webrtc/get_client_config",
        entity_id: this._config.entity,
      });
      const peer = new RTCPeerConnection(clientConfig.configuration);
      this._peer = peer;
      if (clientConfig.dataChannel) peer.createDataChannel(clientConfig.dataChannel);

      this._remoteStream = new MediaStream();
      peer.ontrack = (event) => {
        this._remoteStream.addTrack(event.track);
        if (this._video) {
          this._video.srcObject = this._remoteStream;
          this._video.muted = this._muted;
          this._video.play().catch(() => {
            if (!this._muted) {
              this._muted = true;
              this._video.muted = true;
              this._updateSoundButton();
              this._setStatus("Tap the speaker button to enable audio");
              this._video.play().catch(() => undefined);
            }
          });
        }
      };
      peer.onicecandidate = (event) => this._handleLocalCandidate(event.candidate);
      peer.onconnectionstatechange = () => {
        if (peer.connectionState === "connected") this._setStatus("");
        if (["failed", "disconnected"].includes(peer.connectionState)) {
          this._setStatus(`WebRTC ${peer.connectionState}`);
        }
      };

      this._audioSender = peer.addTransceiver("audio", { direction: "sendrecv" }).sender;
      peer.addTransceiver("video", { direction: "recvonly" });
      const offer = await peer.createOffer({ offerToReceiveAudio: true, offerToReceiveVideo: true });
      await peer.setLocalDescription(offer);

      this._unsubscribe = this._hass.connection.subscribeMessage(
        (event) => this._handleSignal(event),
        { type: "camera/webrtc/offer", entity_id: this._config.entity, offer: offer.sdp }
      );
    } catch (error) {
      this._setStatus(error?.message || String(error));
      await this._cleanup(false);
    } finally {
      this._starting = false;
    }
  }

  async _handleSignal(event) {
    if (!this._peer) return;
    if (event.type === "session") {
      this._sessionId = event.session_id;
      for (const candidate of this._pendingCandidates.splice(0)) {
        await this._sendCandidate(candidate);
      }
    } else if (event.type === "answer") {
      await this._peer.setRemoteDescription({ type: "answer", sdp: event.answer });
    } else if (event.type === "candidate") {
      const candidate = { ...event.candidate };
      if (candidate.sdpMid == null && candidate.sdpMLineIndex == null) candidate.sdpMid = "0";
      await this._peer.addIceCandidate(candidate);
    } else if (event.type === "error") {
      this._setStatus(`WebRTC failed: ${event.message}`);
      await this._cleanup(false);
    }
  }

  async _handleLocalCandidate(candidate) {
    if (!candidate?.candidate) return;
    if (!this._sessionId) {
      this._pendingCandidates.push(candidate.toJSON());
      return;
    }
    await this._sendCandidate(candidate.toJSON());
  }

  _sendCandidate(candidate) {
    return this._hass.callWS({
      type: "camera/webrtc/candidate",
      entity_id: this._config.entity,
      session_id: this._sessionId,
      candidate,
    });
  }

  _beginTalk = async (event) => {
    event.preventDefault();
    if (this._talking || !this._audioSender) return;
    this._talkRequested = true;
    this._talkButton.disabled = true;
    try {
      this._micStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        video: false,
      });
      if (!this._talkRequested) {
        this._micStream.getTracks().forEach((track) => track.stop());
        this._micStream = undefined;
        return;
      }
      const track = this._micStream.getAudioTracks()[0];
      await this._audioSender.replaceTrack(track);
      this._talking = true;
      // Keep inbound audio muted while transmitting to prevent feedback. Once
      // PTT ends, listening is enabled automatically so the reply is audible.
      this._mutedBeforeTalk = false;
      this._muted = true;
      if (this._video) this._video.muted = true;
      if (this._soundButton) this._soundButton.disabled = true;
      this._talkButton.classList.add("active");
      this._talkButton.textContent = "Talking…";
      this._updateSoundButton();
      if (event.pointerId != null) this._talkButton.setPointerCapture?.(event.pointerId);
    } catch (error) {
      this._setStatus(`Microphone unavailable: ${error?.message || error}`);
      await this._stopMicrophone();
    } finally {
      this._talkButton.disabled = false;
    }
  };

  _endTalk = async (event) => {
    event?.preventDefault();
    this._talkRequested = false;
    await this._stopMicrophone();
  };

  _talkKeyDown = (event) => {
    if ((event.key === " " || event.key === "Enter") && !event.repeat) this._beginTalk(event);
  };

  _talkKeyUp = (event) => {
    if (event.key === " " || event.key === "Enter") this._endTalk(event);
  };

  async _stopMicrophone() {
    const restoreMuted = this._talking ? this._mutedBeforeTalk : undefined;
    this._talkRequested = false;
    if (this._audioSender) await this._audioSender.replaceTrack(null).catch(() => undefined);
    this._micStream?.getTracks().forEach((track) => track.stop());
    this._micStream = undefined;
    this._talking = false;
    this._mutedBeforeTalk = undefined;
    if (restoreMuted !== undefined) {
      this._muted = restoreMuted;
      if (this._video) this._video.muted = restoreMuted;
    }
    if (this._soundButton) this._soundButton.disabled = false;
    this._updateSoundButton();
    if (this._talkButton) {
      this._talkButton.classList.remove("active");
      this._talkButton.textContent = "Hold to talk";
    }
  }

  _toggleSound = () => {
    if (!this._video) return;
    this._muted = !this._muted;
    this._video.muted = this._muted;
    this._video.play().catch(() => undefined);
    this._updateSoundButton();
  };

  _updateSoundButton() {
    if (!this._soundButton) return;
    this._soundButton.textContent = this._muted ? "🔇" : "🔊";
    this._soundButton.title = this._muted ? "Enable camera audio" : "Mute camera audio";
    this._soundButton.setAttribute("aria-label", this._soundButton.title);
  }

  async _cleanup(clearStatus = true) {
    await this._stopMicrophone();
    this._remoteStream?.getTracks().forEach((track) => track.stop());
    this._remoteStream = undefined;
    this._peer?.close();
    this._peer = undefined;
    this._audioSender = undefined;
    this._sessionId = undefined;
    this._pendingCandidates = [];
    if (this._video) this._video.srcObject = null;
    if (this._unsubscribe) {
      const unsubscribe = await this._unsubscribe.catch(() => undefined);
      unsubscribe?.();
      this._unsubscribe = undefined;
    }
    if (clearStatus) this._setStatus("");
  }
}

if (!customElements.get("reolink-web-camera-card")) {
  customElements.define("reolink-web-camera-card", ReolinkWebCameraCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "reolink-web-camera-card",
    name: "Reolink Web Camera",
    description: "Reolink FLV camera card with WebRTC push-to-talk",
    preview: true,
    documentationURL: "https://github.com/rsre/HAReolink",
  });
  console.info(`%c REOLINK-WEB-CAMERA-CARD %c ${CARD_VERSION} `, "color:white;background:#067a9c", "color:#067a9c");
}
