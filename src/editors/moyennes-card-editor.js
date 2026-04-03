import BaseEDCardEditor from "./base-editor";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);

const html = LitElement.prototype.html;

class EDMoyennesCardEditor extends BaseEDCardEditor {
  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      ${this.buildEntityPickerField(
        "Cpateur moyennes",
        "entity",
        this._config.entity,
        "moyenne_generale"
      )}
      ${this.buildSwitchField(
        "Display header",
        "display_header",
        this._config.display_header
      )}
      ${this.buildSwitchField(
        "Display class average",
        "display_class_average",
        this._config.display_class_average
      )}
      ${this.buildSwitchField(
        "Compare with class average",
        "compare_with_class_average",
        this._config.compare_with_class_average
      )}
      ${this.buildTextField(
        "Compare with ratio",
        "compare_with_ratio",
        this._config.compare_with_ratio,
        ""
      )}
      ${this.buildSwitchField(
        "Display class min",
        "display_class_min",
        this._config.display_class_min
      )}
      ${this.buildSwitchField(
        "Display class max",
        "display_class_max",
        this._config.display_class_max
      )}
      ${this.buildSwitchField(
        "Display overall average",
        "display_overall_average",
        this._config.display_overall_average,
        true
      )}
    `;
  }
}

customElements.define(
  "ecole_directe-moyennes-card-editor",
  EDMoyennesCardEditor
);
