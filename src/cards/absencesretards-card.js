import BaseEDCard from "./base-card";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class EDAbsencesRetardsCard extends BaseEDCard {
  getAbsencesRetardsRow(absence_retard) {
    let content = html`
      <tr>
        <td class="absence-status">
          <span
            >${absence_retard.justifie
              ? html`<ha-icon icon="mdi:check"></ha-icon>`
              : html`<ha-icon icon="mdi:clock-alert-outline"></ha-icon>`}</span
          >
        </td>
        <td>
          <span
            style="background-color:${absence_retard.justifie
              ? "#107c41"
              : "#e73a1f"}"
          ></span>
        </td>
        <td>
          <span class="absence-from">${absence_retard.display_date}</span
          ><br /><span class="absence-hours">${absence_retard.libelle}</span>
        </td>
        <td>
          <span class="absence-reason">${absence_retard.motif}</span>
        </td>
      </tr>
    `;
    return html`${content}`;
  }

  initCard() {
    let entity_state = this.hass.states[this.config.entity];
    if (entity_state.attributes["Absences"]) {
      this.items_attribute_key = "Absences";
      this.header_title = "Absences de ";
      this.no_data_message = "Aucune absence";
    } else {
      this.items_attribute_key = "Retards";
      this.header_title = "Retards de ";
      this.no_data_message = "Aucun retard";
    }
  }

  getCardContent() {
    const stateObj = this.hass.states[this.config.entity];

    if (stateObj) {
      const absencesRetards = this.getItems();
      const itemTemplates = [];
      let dayTemplates = [];
      for (let index = 0; index < absencesRetards.length; index++) {
        if (this.config.max && this.config.max < index) {
          break;
        }
        dayTemplates.push(this.getAbsencesRetardsRow(absencesRetards[index]));
      }

      if (absencesRetards.length > 0) {
        itemTemplates.push(
          html`<table>
            ${dayTemplates}
          </table>`
        );
      } else {
        itemTemplates.push(this.noDataMessage());
      }

      return itemTemplates;
    }
  }

  getDefaultConfig() {
    return {
      display_header: true,
      max: null,
    };
  }

  static get styles() {
    return css`
      ${super.styles}
      table {
        clear: both;
        font-size: 0.9em;
        font-family: Roboto;
        width: 100%;
        outline: 0px solid #393c3d;
        border-collapse: collapse;
      }
      tr:nth-child(odd) {
        background-color: rgba(0, 0, 0, 0.1);
      }
      td {
        vertical-align: middle;
        padding: 5px 10px 5px 10px;
        text-align: left;
      }
      tr td:first-child {
        width: 10%;
        text-align: right;
      }
      span.absence-reason {
        font-weight: bold;
        display: block;
      }
      tr td:nth-child(2) {
        width: 4px;
        padding: 5px 0;
      }
      tr td:nth-child(2) > span {
        display: inline-block;
        width: 4px;
        height: 3rem;
        border-radius: 4px;
        background-color: grey;
        margin-top: 4px;
      }
      span.absence-from {
        font-weight: bold;
        padding: 4px;
        border-radius: 4px;
      }
      span.absence-hours {
        font-size: 0.9em;
        padding: 4px;
      }
      table + div {
        border-top: 1px solid white;
      }
    `;
  }

  static getStubConfig() {
    return {
      display_header: true,
      max: null,
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-absences-retards-card-editor");
  }
}

customElements.define(
  "ecole_directe-absences-retards-card",
  EDAbsencesRetardsCard
);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-absences-retards-card",
  name: "Carte Absences/Retards pour Ecole Directe",
  description: "Affiche les absences ou les retards pour Ecole Directe",
  documentationURL:
    "https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#absences",
});
