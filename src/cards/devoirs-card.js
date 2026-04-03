import BaseEDCard from "./base-card";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

Date.prototype.getWeekNumber = function () {
  var d = new Date(+this);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 4 - (d.getDay() || 7));
  return Math.ceil(((d - new Date(d.getFullYear(), 0, 1)) / 8.64e7 + 1) / 7);
};

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

  getdevoirRow(devoir, index) {
    let description = devoir.description.trim().replace("\n", "<br />");

    return html`
      <tr class="${devoir.effectue ? "devoir-done" : ""}">
        <td class="devoir-detail">
          <label for="devoir-${index}">
            <span class="devoir-subject">${devoir.matiere}</span>
            ${devoir.interrogation
              ? html`<span class="devoir-controle">(Contrôle)</span>`
              : html``}
          </label>
          <input type="checkbox" id="devoir-${index}" />
          <span class="devoir-description">${unsafeHTML(description)}</span>
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
      const devoir = stateObj.attributes["Devoirs"];
      if (devoir) {
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
      .reduce-done .devoir-done .devoir-description {
        display: none;
      }
      .reduce-done .devoir-done input:checked + .devoir-description {
        display: block;
      }
      .devoir-detail input {
        display: none;
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
