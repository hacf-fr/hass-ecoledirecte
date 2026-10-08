import BaseEDCard from "./base-card";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

(Date.prototype as any).getWeekNumber = function () {
  var d = new Date(+(this as any));
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 4 - (d.getDay() || 7));
  return Math.ceil((((d as any) - (new Date(d.getFullYear(), 0, 1) as any)) / 8.64e7 + 1) / 7);
};

const AUDIO_EXTENSIONS = ["mp3", "m4a", "aac", "wav", "ogg", "oga", "opus", "flac"];
const VIDEO_EXTENSIONS = ["mp4", "webm", "mov", "m4v"];

class EDDevoirCard extends BaseEDCard {
  lunchBreakRendered = false;

  initCard() {}

  getFormattedDate(date) {
    return new Date(date)
      .toLocaleDateString("fr-FR", {
        weekday: "long",
        day: "2-digit",
        month: "2-digit",
      })
      .replace(/^(.)/, (match) => match.toUpperCase());
  }

  getDayHeader(devoir, daysCount) {
    return html`<div class="ed-devoir-header">
      ${this.config.enable_slider
        ? html`<span
            class="ed-devoir-header-arrow-left ${daysCount === 0
              ? "disabled"
              : ""}"
            @click=${(e) => this.changeDay("previous", e)}
            >←</span
          >`
        : ""}
      <span class="ed-devoir-header-date"
        >${this.getFormattedDate(devoir.date)}</span
      >
      ${this.config.enable_slider
        ? html`<span
            class="ed-devoir-header-arrow-right"
            @click=${(e) => this.changeDay("next", e)}
            >→</span
          >`
        : ""}
    </div>`;
  }

  changeDay(direction, e) {
    e.preventDefault();
    if (e.target.classList.contains("disabled")) {
      return;
    }

    const activeDay = e.target.parentElement.parentElement;
    let hasPreviousDay =
      activeDay.previousElementSibling &&
      activeDay.previousElementSibling.classList.contains(
        "ed-devoir-day-wrapper"
      );
    let hasNextDay =
      activeDay.nextElementSibling &&
      activeDay.nextElementSibling.classList.contains("ed-devoir-day-wrapper");
    let newActiveDay = null;

    if (direction === "previous" && hasPreviousDay) {
      newActiveDay = activeDay.previousElementSibling;
    } else if (direction === "next" && hasNextDay) {
      newActiveDay = activeDay.nextElementSibling;
    }

    if (newActiveDay) {
      activeDay.classList.remove("active");
      newActiveDay.classList.add("active");

      hasPreviousDay =
        newActiveDay.previousElementSibling &&
        newActiveDay.previousElementSibling.classList.contains(
          "ed-devoir-day-wrapper"
        );
      hasNextDay =
        newActiveDay.nextElementSibling &&
        newActiveDay.nextElementSibling.classList.contains(
          "ed-devoir-day-wrapper"
        );

      if (!hasPreviousDay) {
        newActiveDay
          .querySelector(".ed-devoir-header-arrow-left")
          .classList.add("disabled");
      }

      if (!hasNextDay) {
        newActiveDay
          .querySelector(".ed-devoir-header-arrow-right")
          .classList.add("disabled");
      }
    }
  }

  getMediaKind(libelle) {
    const extension = String(libelle || "").split(".").pop().toLowerCase();
    if (AUDIO_EXTENSIONS.includes(extension)) {
      return "audio";
    }
    if (VIDEO_EXTENSIONS.includes(extension)) {
      return "video";
    }
    return "file";
  }

  // URL signée : le navigateur télécharge / lit le document en flux,
  // sans le garder en mémoire côté JavaScript.
  async getDocumentUrl(document, download) {
    const res: any = await this.hass.callWS({
      type: "auth/sign_path",
      path: `/api/ecole_directe/document/${encodeURIComponent(document.id)}${
        download ? "?download=1" : ""
      }`,
      expires: 3600,
    });
    return this.hass.hassUrl(res.path);
  }

  setDocumentState(document, state) {
    this._documentStates = { ...(this._documentStates || {}), [document.id]: state };
    this.requestUpdate();
  }

  async downloadDocument(document, e) {
    e.preventDefault();
    e.stopPropagation();
    this.setDocumentState(document, "loading");
    try {
      const link = window.document.createElement("a");
      link.href = await this.getDocumentUrl(document, true);
      link.download = document.libelle || "";
      link.rel = "noopener";
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      this.setDocumentState(document, null);
    } catch (err) {
      console.error("Error downloading document", document.id, err);
      this.setDocumentState(document, "error");
    }
  }

  async playDocument(document, kind, e) {
    e.preventDefault();
    e.stopPropagation();
    const alreadyOpen = this._player && this._player.id === document.id;
    // Un seul lecteur ouvert à la fois
    this.closePlayer();
    if (alreadyOpen) {
      return;
    }
    this.setDocumentState(document, "loading");
    try {
      const url = await this.getDocumentUrl(document, false);
      this._player = { id: document.id, kind, url };
      this.setDocumentState(document, null);
    } catch (err) {
      console.error("Error opening document", document.id, err);
      this.setDocumentState(document, "error");
    }
  }

  closePlayer(e = null) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    // Arrêter la lecture et libérer le tampon du navigateur
    const media = this.shadowRoot?.querySelector<HTMLMediaElement>(
      ".devoir-document-player audio, .devoir-document-player video"
    );
    if (media) {
      media.pause();
      media.removeAttribute("src");
      media.load();
    }
    if (this._player) {
      this._player = null;
      this.requestUpdate();
    }
  }

  disconnectedCallback() {
    this.closePlayer();
    super.disconnectedCallback();
  }

  getDocumentRow(document) {
    const kind = this.getMediaKind(document.libelle);
    const state = this._documentStates?.[document.id];
    const player =
      this._player && this._player.id === document.id ? this._player : null;
    const icon =
      kind === "audio"
        ? "mdi:file-music-outline"
        : kind === "video"
          ? "mdi:file-video-outline"
          : "mdi:file-document-outline";

    return html`
      <div class="devoir-document">
        <span
          class="devoir-document-link"
          title="${kind === "file" ? "Télécharger" : "Lire"}"
          @click=${(e) =>
            kind === "file"
              ? this.downloadDocument(document, e)
              : this.playDocument(document, kind, e)}
        >
          <ha-icon icon="${icon}"></ha-icon>
          <span>${document.libelle}</span>
        </span>
        ${kind !== "file"
          ? html`<ha-icon
              class="devoir-document-action"
              icon="mdi:download"
              title="Télécharger"
              @click=${(e) => this.downloadDocument(document, e)}
            ></ha-icon>`
          : html``}
        ${state === "loading"
          ? html`<span class="devoir-document-status">Chargement…</span>`
          : state === "error"
            ? html`<span class="devoir-document-status error">Erreur</span>`
            : html``}
      </div>
      ${player
        ? html`<div class="devoir-document-player">
            ${player.kind === "audio"
              ? html`<audio controls autoplay src="${player.url}"></audio>`
              : html`<video
                  controls
                  autoplay
                  playsinline
                  src="${player.url}"
                ></video>`}
            <ha-icon
              class="devoir-document-action"
              icon="mdi:close"
              title="Fermer"
              @click=${(e) => this.closePlayer(e)}
            ></ha-icon>
          </div>`
        : html``}
    `;
  }

  getdevoirRow(devoir, index) {
    if (!devoir) {
      return html``;
    }
    const rawDesc = devoir.description || devoir.short_description || "";
    const description = (typeof rawDesc === "string" ? rawDesc : String(rawDesc))
      .trim()
      .replace(/\n/g, "<br />");

    return html`
      <tr class="${devoir.effectue ? "devoir-done" : ""}">
        <td class="devoir-detail">
          <label for="devoir-${index}">
            <span class="devoir-subject">${devoir.matiere || ""}</span>
            ${devoir.interrogation
              ? html`<span class="devoir-controle">(Contrôle)</span>`
              : html``}
          </label>
          <input type="checkbox" id="devoir-${index}" />
          <span class="devoir-description">${unsafeHTML(description)}</span>
          ${Array.isArray(devoir.documents) && devoir.documents.length > 0
            ? html`
                <div class="devoir-documents">
                  <ha-icon icon="mdi:file-document-multiple-outline"></ha-icon>
                  <span>
                    ${devoir.documents.length} document${devoir.documents.length > 1 ? "s" : ""}
                  </span>
                </div>

                <div class="devoir-document-list">
                  ${devoir.documents.map((d) => this.getDocumentRow(d))}
                </div>
              `
            : html``}
        </td>
        <td class="devoir-status">
          <span
            >${devoir.effectue
              ? html`<ha-icon icon="mdi:check"></ha-icon>`
              : html`<ha-icon icon="mdi:account-clock"></ha-icon>`}</span
          >
        </td>
      </tr>
    `;
  }

  getDayRow(devoir, dayTemplates, daysCount) {
    return html`
      <div
        class="${this.config.enable_slider
          ? "slider-enabled"
          : ""} ed-devoir-day-wrapper ${daysCount === 0 ? "active" : ""}"
      >
        ${this.getDayHeader(devoir, daysCount)}
        <table class="${this.config.reduce_done_devoir ? "reduce-done" : ""}">
          ${dayTemplates}
        </table>
      </div>
    `;
  }

  render() {
    if (!this.config || !this.hass) {
      return html`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`;
    }

    const stateObj = this.hass.states[this.config.entity];

    if (stateObj) {
      let devoir = stateObj.attributes["Devoirs"];
      if (devoir) {
        if (devoir.length > 0 && devoir[0].stored_in_store) {
          const storeKey = devoir[0].store_key;
          if (this._storedData && this._storedData[storeKey]) {
            devoir = this._storedData[storeKey];
          } else {
            if (!this._fetchingKeys) this._fetchingKeys = {};
            if (!this._fetchingKeys[storeKey]) {
              this._fetchingKeys[storeKey] = true;
              this.hass
                .callWS({
                  type: "ecole_directe/get_stored_data",
                  key: storeKey,
                })
                .then((res: any) => {
                  if (!this._storedData) this._storedData = {};
                  this._storedData[storeKey] = res.data || [];
                  this.requestUpdate();
                })
                .catch((err: any) => {
                  console.error("Error fetching stored data for key", storeKey, err);
                });
            }
            return html`<div class="ed-card-no-data">Chargement des devoirs...</div>`;
          }
        }
        const itemTemplates = [];
        let dayTemplates = [];
        let daysCount = 0;

        if (devoir && devoir.length > 0) {
          if (devoir[0].Erreur) {
            return html`<div class="ed-card-no-data">${devoir[0].Erreur}</div>`;
          }
          let latestdevoirDay = this.getFormattedDate(devoir[0].date);
          for (let index = 0; index < devoir.length; index++) {
            let hw = devoir[index];
            let currentFormattedDate = this.getFormattedDate(hw.date);

            if (
              hw.effectue === true &&
              this.config.display_done_devoir === false
            ) {
              continue;
            }

            // if devoir for a new day
            if (latestdevoirDay !== currentFormattedDate) {
              // if previous day has lessons
              if (dayTemplates.length > 0) {
                itemTemplates.push(
                  this.getDayRow(devoir[index - 1], dayTemplates, daysCount)
                );
                dayTemplates = [];
              }

              latestdevoirDay = currentFormattedDate;
              daysCount++;
            }

            dayTemplates.push(this.getdevoirRow(hw, index));
          }

          // if there are devoir for the day and not limit on the current week or limit and current week
          if (dayTemplates.length > 0) {
            itemTemplates.push(
              this.getDayRow(devoir[devoir.length - 1], dayTemplates, daysCount)
            );
          }
        }

        if (itemTemplates.length === 0) {
          itemTemplates.push(this.noDataMessage());
        }

        return html` <ha-card
          id="${this.config.entity}-card"
          class="${this.config.enable_slider ? "ed-devoir-card-slider" : ""}"
        >
          ${this.config.display_header ? this.getCardHeader() : ""}
          ${itemTemplates}
        </ha-card>`;
      }
    }

    return html`<div class="ed-card-no-data">
      Veuillez choisir une autre entité
    </div>`;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Vous devez définir une entité");
    }

    const defaultConfig = {
      entity: null,
      display_header: true,
      reduce_done_devoir: true,
      display_done_devoir: true,
      enable_slider: false,
    };

    this.config = {
      ...defaultConfig,
      ...config,
    };

    this.header_title = "Devoirs de ";
    this.no_data_message = "Pas de devoirs à faire";
  }

  static get styles() {
    return css`
      ${super.styles}
      .ed-devoir-card-slider .ed-devoir-day-wrapper {
        display: none;
      }
      .ed-devoir-card-slider .ed-devoir-day-wrapper.active {
        display: block;
      }
      .ed-devoir-card-slider .ed-devoir-header-date {
        display: inline-block;
        text-align: center;
        width: 120px;
      }
      .ed-devoir-header-arrow-left,
      .ed-devoir-header-arrow-right {
        cursor: pointer;
      }
      .ed-devoir-header-arrow-left.disabled,
      .ed-devoir-header-arrow-right.disabled {
        opacity: 0.3;
        pointer-events: none;
      }
      div:not(.slider-enabled) > .ed-devoir-header {
        border-bottom: 2px solid grey;
      }
      .slider-enabled > .ed-devoir-header {
        padding-top: 0;
        text-align: center;
      }
      table {
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      td {
        vertical-align: top;
        padding: 5px 10px 5px 10px;
        padding-top: 8px;
        text-align: left;
      }
      td.devoir-detail {
        padding: 0;
        padding-top: 8px;
        padding-bottom: 8px;
      }
      span.devoir-subject {
        display: block;
        font-weight: bold;
      }
      span.devoir-controle {
        display: block;
        font-weight: bold;
        color: red;
      }
      span.devoir-description {
        font-size: 0.9em;
      }
      td.devoir-status {
        width: 5%;
      }
      .reduce-done .devoir-done label:hover {
        cusor: pointer;
      }
      .reduce-done .devoir-done .devoir-description,
      .reduce-done .devoir-done .devoir-documents,
      .reduce-done .devoir-done .devoir-document-list {
        display: none;
      }
      .reduce-done .devoir-done input:checked + .devoir-description {
        display: block;
      }
      .reduce-done .devoir-done input:checked ~ .devoir-documents {
        display: flex;
      }
      .reduce-done .devoir-done input:checked ~ .devoir-document-list {
        display: block;
      }
      .devoir-detail input {
        display: none;
      }
      .devoir-documents {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-top: 3px;
        padding-top: 0px;
        padding-top: 2px;
        padding-bottom: 2px;
        padding-left: 0px;
        font-size: 0.85em;
        opacity: 0.8;
      }
      .devoir-documents ha-icon {
        --mdc-icon-size: 18px;
      }
      .devoir-document-list {
        margin-top: 5px;
        margin-left: 0px;
        padding-top: 0px;
        padding-left: 4px;
      }
      .devoir-document {
        display: flex;
        align-items: flex-start;
        gap: 6px;
        margin: 0px;
        padding: 0px;
        padding-left: 4px;
        font-size: 0.82em;
        opacity: 0.85;
      }
      .devoir-document ha-icon {
        flex-shrink: 0;
        --mdc-icon-size: 16px;
      }
      .devoir-document-link {
        display: flex;
        align-items: flex-start;
        gap: 6px;
        cursor: pointer;
      }
      .devoir-document-link:hover span {
        text-decoration: underline;
      }
      .devoir-document-action {
        cursor: pointer;
      }
      .devoir-document-status {
        font-style: italic;
        opacity: 0.8;
      }
      .devoir-document-status.error {
        color: var(--error-color, red);
      }
      .devoir-document-player {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 0 4px 4px;
      }
      .devoir-document-player audio,
      .devoir-document-player video {
        flex: 1;
        min-width: 0;
        max-width: 100%;
      }
      .devoir-document-player ha-icon {
        --mdc-icon-size: 18px;
      }
    `;
  }

  static getStubConfig() {
    return {
      display_header: true,
      reduce_done_devoir: true,
      display_done_devoir: true,
      enable_slider: false,
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-devoirs-card-editor");
  }
}

customElements.define("ecole_directe-devoirs-card", EDDevoirCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-devoirs-card",
  name: "Carte des devoirs pour Ecole Directe",
  description: "Affiche les devoirs pour Ecole Directe",
  documentationURL:
    "https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#devoirs",
});
