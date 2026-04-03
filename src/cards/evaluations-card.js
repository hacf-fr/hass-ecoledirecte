import BaseEDCard from "./base-card";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class EDEvaluationsCard extends BaseEDCard {
  initCard() {
    this.items_attribute_key = "Evaluations";
    this.header_title = "Evaluations de ";
    this.no_data_message = "Pas d'évaluation à afficher";
  }

  getFormattedDate(date) {
    return new Date(date)
      .toLocaleDateString("fr-FR", {
        weekday: "short",
        day: "2-digit",
        month: "2-digit",
      })
      .replace(/^(.)/, (match) => match.toUpperCase());
  }

  getAcquisitionRow(acquisition) {
    return html`<tr class="acquisition-row">
      <td>${acquisition.competence}</td>
      <td>${this.getAcquisitionIcon(acquisition)}</td>
    </tr>`;
  }

  getAcquisitionIcon(acquisition) {
    const remappedEvaluations =
      this.config.mapping_evaluations[acquisition.valeur] || acquisition.valeur;
    let icon = "";
    if (remappedEvaluations === "A+") {
      icon = "+";
    } else if (remappedEvaluations === "Abs") {
      icon = "a";
    }
    return html`
      <span
        title="${acquisition.descriptif}"
        class="acquisition-icon acquisition-icon-${remappedEvaluations}"
      >
        ${icon}
      </span>
    `;
  }

  getEvaluationRow(evaluation, index) {
    let acquisitions = evaluation.elements_programme;
    let acquisitionIcons = [];
    let acquisitionsRows = [];
    let lesson_background_color = "grey";

    for (let i = 0; i < acquisitions.length; i++) {
      acquisitionIcons.push(this.getAcquisitionIcon(acquisitions[i]));
      acquisitionsRows.push(this.getAcquisitionRow(acquisitions[i]));
    }

    return html`
      <tr class="evaluation-row">
        <td class="evaluation-color">
          <span style="background-color:${lesson_background_color}"></span>
        </td>
        <td class="evaluation-description">
          <label for="evaluation-full-detail-${index}">
            <span class="evaluation-subject">${evaluation.matiere}</span>
          </label>
          <input type="checkbox" id="evaluation-full-detail-${index}" />
          ${this.config.display_comment
            ? html`<span class="evaluation-comment">${evaluation.devoir}</span>`
            : ""}
          ${this.config.display_date
            ? html`<span class="evaluation-date"
                >${this.getFormattedDate(evaluation.date)}</span
              >`
            : ""}
        </td>
        <td class="evaluation-detail">${acquisitionIcons}</td>
      </tr>
      ${acquisitionsRows}
    `;
  }

  getCardContent() {
    const stateObj = this.hass.states[this.config.entity];

    if (stateObj) {
      const evaluations = this.getItems();
      const max_evaluations = this.config.max_evaluations ?? evaluations.length;

      const evaluationsRows = [];
      const itemTemplates = [];

      for (let index = 0; index < max_evaluations; index++) {
        if (index >= evaluations.length) {
          break;
        }
        let evaluation = evaluations[index];
        evaluationsRows.push(
          // this.getEvaluationRow(evaluation, index, lessons_colors)
          this.getEvaluationRow(evaluation, index)
        );
      }

      if (evaluationsRows.length > 0) {
        itemTemplates.push(
          html`<table>
            ${evaluationsRows}
          </table>`
        );
      } else {
        itemTemplates.push(this.noDataMessage());
      }

      return itemTemplates;
    }

    return [];
  }

  getDefaultConfig() {
    return {
      display_header: true,
      display_description: true,
      display_teacher: true,
      display_date: true,
      display_comment: true,
      max_evaluations: null,
      mapping_evaluations: {},
    };
  }

  static get styles() {
    return css`
      ${super.styles}
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
        text-align: left;
      }
      td.evaluation-color {
        width: 4px;
        padding-top: 11px;
      }
      td.evaluation-color > span {
        display: inline-block;
        width: 4px;
        height: 2rem;
        border-radius: 4px;
        background-color: grey;
      }
      .above-average .evaluation-color > span,
      .above-ratio .evaluation-color > span {
        background-color: green;
      }
      .below-average .evaluation-color > span,
      .below-ratio .evaluation-color > span {
        background-color: orange;
      }
      .evaluation-subject {
        font-weight: bold;
        display: block;
      }
      .evaluation-description {
        display: block;
      }
      .evaluation-teacher {
        display: block;
      }
      .evaluation-date,
      .evaluation-coefficient {
        font-size: 0.9em;
        color: gray;
      }
      .evaluation-comment {
        display: block;
      }
      .evaluation-date + .evaluation-coefficient:before {
        content: " - ";
      }
      .evaluation-detail {
        text-align: right;
      }
      .evaluation-value {
        font-weight: bold;
      }
      .acquisition-icon {
        display: inline-block;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: solid 0.02em rgba(0, 0, 0, 0.5);
        margin-left: 4px;
        vertical-align: middle;
        color: white;
        content: "+";
        text-align: center;
        line-height: 14px;
      }
      .acquisition-icon-4 {
        background-color: rgb(0, 176, 80);
      }
      .acquisition-icon-3 {
        background-color: rgb(0, 112, 192);
      }
      .acquisition-icon-2 {
        background-color: rgb(255, 192, 0);
      }
      .acquisition-icon-1 {
        background-color: #f80a0a;
      }
      .acquisition-row {
        display: none;
      }
      input[type="checkbox"] {
        display: none;
      }
      /** FIXME
        .evaluation-row:has(input:checked) .acquisition-icon {
            display:none;
        }
        .evaluation-row:has(input:checked) + .acquisition-row {
            display: table-row;
        }
        */
      .acquisition-row td:nth-child(2) {
        text-align: right;
      }
    `;
  }

  static getStubConfig() {
    return {
      display_header: true,
      display_description: true,
      display_teacher: true,
      display_date: true,
      display_comment: true,
      max_evaluations: null,
      mapping_evaluations: {},
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-evaluations-card-editor");
  }
}

customElements.define("ecole_directe-evaluations-card", EDEvaluationsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-evaluations-card",
  name: "Carte des évaluations pour Ecole Directe",
  description: "Affiche les évaluations pour Ecole Directe",
  documentationURL:
    "https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#evaluations",
});
