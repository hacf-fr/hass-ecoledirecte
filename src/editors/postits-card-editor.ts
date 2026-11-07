import BaseEDCardEditor from "./base-editor";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;

class EDPostitsCardEditor extends BaseEDCardEditor {
  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    return html`
      ${this.buildEntityPickerField(
        "Espace de travail",
        "entity",
        this._config.entity,
        "(espace|workspace)"
      )}
      ${this.buildSwitchField(
        "Display header",
        "display_header",
        this._config.display_header,
        true
      )}
      ${this.buildSelectField(
        "Format du contenu",
        "allow_html",
        [
          { value: "text", label: "Texte uniquement" },
          { value: "sanitize", label: "HTML assaini" },
          {
            value: "full_html",
            label: "HTML complet (non assaini, risque de sécurité)",
          },
        ],
        this._config.allow_html === true
          ? "sanitize"
          : this._config.allow_html || "text"
      )}
      ${this.buildNumberField(
        "Nombre de post-it",
        "max_postits",
        this._config.max_postits ?? 2,
        0,
        1
      )}
    `;
  }
}

customElements.define(
  "ecole_directe-postits-card-editor",
  EDPostitsCardEditor
);
