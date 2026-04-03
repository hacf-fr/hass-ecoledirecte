import BaseEDCard from "./base-card";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class EDMoyennesCard extends BaseEDCard {
  initCard() {
    this.items_attribute_key = "Disciplines";
    this.header_title = "Moyennes de ";
    this.no_data_message = "Aucune moyenne";
  }

  getOverallAverageRow() {
    let overall_average_entity = `${this.config.entity}`;

    if (!this.hass.states[overall_average_entity]) {
      return html``;
    }

    let overall_average = this.hass.states[overall_average_entity].state;

    if (!overall_average) {
      return html``;
    }

    let average = parseFloat(overall_average.replace(",", "."));
    let average_classes = [];

    if (this.config.compare_with_ratio !== null) {
      let comparison_ratio = parseFloat(this.config.compare_with_ratio);
      average_classes.push(
        average >= comparison_ratio ? "above-ratio" : "below-ratio"
      );
    }

    return html`
      <tr class="${average_classes.join(" ")} overall-average">
        <td class="average-color"><span></span></td>
        <td class="average-description">
          <span class="average-subject">Moyenne générale</span>
        </td>
        <td class="average-detail">
          <span class="average-value"
            ><span>${overall_average.replace(".", ",")}</span></span
          >
        </td>
      </tr>
    `;
  }

  getAverageRow(averageData) {
    let average = parseFloat(averageData.moyenne.replace(",", "."));

    let average_classes = [];

    if (this.config.compare_with_ratio !== null) {
      let comparison_ratio = parseFloat(this.config.compare_with_ratio);
      average_classes.push(
        average >= comparison_ratio ? "above-ratio" : "below-ratio"
      );
    } else if (
      this.config.compare_with_class_average &&
      averageData.moyenneClasse
    ) {
      let class_average = parseFloat(
        averageData.moyenneClasse.replace(",", ".")
      );
      average_classes.push(
        average > class_average ? "above-average" : "below-average"
      );
    }

    return html`
      <tr class="${average_classes.join(" ")}">
        <td class="average-color">
          <span style="background-color:Grey"></span>
        </td>
        <td class="average-description">
          <span class="average-subject">${averageData.nom}</span>
        </td>
        <td class="average-detail">
          <span class="average-value">${averageData.moyenne}</span>
          ${this.config.display_class_average && averageData.moyenneClasse
            ? html`<span class="average-class-average"
                >Classe ${averageData.moyenneClasse}</span
              >`
            : ""}
          ${this.config.display_class_min && averageData.moyenneMin
            ? html`<span class="average-class-min"
                >Min. ${averageData.moyenneMin}</span
              >`
            : ""}
          ${this.config.display_class_max && averageData.moyenneMax
            ? html`<span class="average-class-max"
                >Max. ${averageData.moyenneMax}</span
              >`
            : ""}
        </td>
      </tr>
    `;
  }

  getCardContent() {
    const stateObj = this.hass.states[this.config.entity];

    if (stateObj) {
      const moyennes = this.getItems();
      const itemTemplates = [];
      const moyennesRows = [];

      if (this.config.display_overall_average) {
        moyennesRows.push(this.getOverallAverageRow(moyennes));
      }

      for (let index = 0; index < moyennes.length; index++) {
        let average = moyennes[index];
        moyennesRows.push(this.getAverageRow(average));
      }

      if (moyennesRows.length > 0) {
        itemTemplates.push(
          html`<table>
            ${moyennesRows}
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
      display_class_average: true,
      compare_with_class_average: true,
      compare_with_ratio: null,
      display_class_min: true,
      display_class_max: true,
      display_overall_average: true,
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
        padding-top: 8px;
        text-align: left;
      }
      tr.overall-average {
        border-bottom: 1px solid #393c3d;
      }
      tr.overall-average td {
        text-transform: uppercase;
        padding-bottom: 10px;
      }
      tr.overall-average .average-value span {
        padding: 5px;
        border-radius: 5px;
        border: 1px solid var(--primary-text-color);
      }
      tr.overall-average tr td {
        padding-top: 10px;
      }
      td.average-comparison-color,
      td.average-color {
        width: 4px;
        padding-top: 11px;
      }
      td.average-comparison-color > span,
      td.average-color > span {
        display: inline-block;
        width: 4px;
        height: 1rem;
        border-radius: 4px;
        background-color: grey;
      }

      .above-average .average-detail,
      .above-ratio .average-detail,
      .below-average .average-detail,
      .below-ratio .average-detail {
        position: relative;
      }
      .above-average span.average-value,
      .above-ratio span.average-value,
      .below-average span.average-value,
      .below-ratio span.average-value {
        padding-right: 16px;
      }
      .above-average span.average-value:before,
      .above-ratio span.average-value:before,
      .below-average span.average-value:before,
      .below-ratio span.average-value:before {
        content: " ";
        display: block;
        width: 10px;
        height: 10px;
        border-radius: 5px;
        position: absolute;
        right: 10px;
        top: 13px;
      }
      .above-average span.average-value:before,
      .above-ratio span.average-value:before {
        background-color: green;
      }
      .below-average span.average-value:before,
      .below-ratio span.average-value:before {
        background-color: orange;
      }
      .average-description {
        padding-left: 0;
      }
      .average-subject {
        display: inline-block;
        font-weight: bold;
        position: relative;
      }
      .average-detail {
        text-align: right;
      }
      .average-value {
        font-weight: bold;
      }
      .average-value,
      .average-class-average {
        display: block;
      }
      .average-class-average,
      .average-class-min,
      .average-class-max {
        font-size: 0.9em;
        color: gray;
      }
      .average-class-min + .average-class-max:before {
        content: " - ";
      }
    `;
  }

  static getStubConfig() {
    return {
      display_header: true,
      display_class_average: true,
      compare_with_class_average: true,
      compare_with_ratio: null,
      display_class_min: true,
      display_class_max: true,
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-moyennes-card-editor");
  }
}

customElements.define("ecole_directe-moyennes-card", EDMoyennesCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-moyennes-card",
  name: "Carte des moyennes pour Ecole Directe",
  description: "Affiche les moyennes pour Ecole Directe",
  documentationURL:
    "https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#moyennes",
});
