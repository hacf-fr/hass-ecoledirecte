const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
) as typeof HTMLElement;
const html = (LitElement as any).prototype.html;
const css = (LitElement as any).prototype.css;

class BaseEDCardEditor extends LitElement {
  [key: string]: any;

  static get properties() {
    return {
      hass: {},
      _config: {},
    };
  }

  setConfig(config) {
    this._config = config;
    this.loadEntityPicker();
  }

  _valueChanged(ev) {
    const _config = Object.assign({}, this._config);

    if (typeof ev.target.checked !== "undefined") {
      _config[ev.target.configValue] = ev.target.checked;
    } else {
      _config[ev.target.configValue] =
        ev.target.value == "" ? null : ev.target.value;
    }

    this._config = _config;

    const event = new CustomEvent("config-changed", {
      detail: { config: _config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  buildSelectField(label: any, config_key: any, options: any, value: any, default_value?: any) {
    let selectOptions = [];
    for (let i = 0; i < options.length; i++) {
      let currentOption = options[i];
      selectOptions.push(
        html`<ha-list-item .value="${currentOption.value}"
          >${currentOption.label}</ha-list-item
        >`
      );
    }

    return html`
      <ha-select
        label="${label}"
        .value=${value || default_value}
        .configValue=${config_key}
        @change=${this._valueChanged}
        @closed=${(ev: any) => ev.stopPropagation()}
      >
        ${selectOptions}
      </ha-select>
    `;
  }

  buildSwitchField(label: any, config_key: any, value: any, default_value?: any) {
    if (typeof value !== "boolean") {
      value = default_value;
    }

    return html`
      <ha-formfield class="switch-wrapper" .label="${label}">
        <ha-switch
          name="${config_key}"
          .checked=${value}
          .configValue="${config_key}"
          @change=${this._valueChanged}
        ></ha-switch>
      </ha-formfield>
    `;
  }

  buildNumberField(label: any, config_key: any, value: any, default_value?: any, step?: any) {
    return html`
      <ha-textfield
        type="number"
        step="${step || 1}"
        label="${label}"
        .value=${value || default_value}
        .configValue=${config_key}
        @change=${this._valueChanged}
      >
      </ha-textfield>
    `;
  }

  buildTextField(label: any, config_key: any, value: any, default_value?: any) {
    return html`
      <ha-textfield
        label="${label}"
        .value=${value || default_value}
        .configValue=${config_key}
        @change=${this._valueChanged}
        @keyup=${this._valueChanged}
      >
      </ha-textfield>
    `;
  }

  buildEntityPickerField(label: any, config_key: any, value: any, filter: any) {
    const entityFilter = new RegExp("ed_(.*)_" + filter);

    return html`
      <ha-entity-picker
        label="${label}"
        .hass=${this.hass}
        .value=${value || ""}
        .configValue=${config_key}
        .includeDomains="sensor"
        .entityFilter="${(entity) => entityFilter.test(entity.entity_id)}"
        @value-changed=${this._valueChanged}
        allow-custom-entity
      ></ha-entity-picker>
    `;
  }

  async loadEntityPicker() {
    if (window.customElements.get("ha-entity-picker")) {
      return;
    }

    const ch = await window.loadCardHelpers();
    const c = await ch.createCardElement({ type: "entities", entities: [] });
    await c.constructor.getConfigElement();
  }

  static get styles() {
    return css`
      ha-formfield {
        display: block;
        padding-top: 20px;
        clear: right;
      }
      ha-formfield > ha-switch {
        float: right;
      }
      ha-select,
      ha-textfield {
        clear: right;
        width: 100%;
        padding-top: 15px;
      }
    `;
  }
}

export default BaseEDCardEditor;
