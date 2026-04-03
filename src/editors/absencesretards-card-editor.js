import BaseEDCardEditor from "./base-editor";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);

const html = LitElement.prototype.html;

class EDAbsencesRetardsCardEditor extends BaseEDCardEditor {
  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      ${this.buildEntityPickerField(
        "Absences/Retards entity",
        "entity",
        this._config.entity,
        "(absences|retards)"
      )}
      ${this.buildSwitchField(
        "Display header",
        "display_header",
        this._config.display_header
      )}
      ${this.buildNumberField("Max", "max", this._config.max)}
    `;
  }
}

customElements.define(
  "ecole_directe-absences-retards-card-editor",
  EDAbsencesRetardsCardEditor
);
