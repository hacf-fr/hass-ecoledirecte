import BaseEDCard from "./base-card";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

const CLOUD_ACTION_LABELS = {
  ajoutDossier: "Ajout d'un dossier",
  ajoutFichier: "Ajout d'un fichier",
  suppressionFich: "Vidage corbeille d'un fichier",
  suppressionDoss: "Vidage corbeille d'un dossier",
  renommeDossier: "Renommage d'un dossier",
  renommeFichier: "Renommage d'un fichier",
  sendToTrashDoss: "Mise à la corbeille d'un dossier",
  sendToTrashFich: "Mise à la corbeille d'un fichier",
  restauDoss: "Restauration d'un dossier",
  restauFich: "Restauration d'un fichier",
};

class EDWorkspaceCard extends BaseEDCard {
  initCard() {}

  render() {
    if (!this.config || !this.hass) {
      return html`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`;
    }

    if (!this.hass.states[this.config.entity]) {
      return html`<div class="ed-card-no-data">
        Veuillez choisir une autre entité
      </div>`;
    }

    this.initCard();
    const fullHtml = this.getHtmlMode() === "full_html";
    const cardStyle = this.getCardStyle(fullHtml);
    return html`<ha-card
      id="${this.config.entity}-card"
      class="${fullHtml ? "full-html" : ""}"
      style="${cardStyle}"
    >
      ${this.config.display_header ? this.getCardHeader() : ""}
      ${this.getCardContent()}
    </ha-card>`;
  }

  getCardStyle(fullHtml) {
    return "";
  }

  getHtmlMode() {
    if (
      this.config.allow_html === "full_html" ||
      this.config.allow_html === "sanitize"
    ) {
      return this.config.allow_html;
    }
    return "text";
  }

  decodeContent(content, htmlMode = "text") {
    const normalized = content
      .replace(/\s+/g, "")
      .replace(/-/g, "+")
      .replace(/_/g, "/");
    let decoded = content;
    if (
      normalized.length > 0 &&
      normalized.length % 4 !== 1 &&
      /^[A-Za-z0-9+/]*={0,2}$/.test(normalized)
    ) {
      try {
        const binary = atob(
          normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=")
        );
        const bytes = Uint8Array.from(binary, (character) =>
          character.charCodeAt(0)
        );
        const base64Decoded = new TextDecoder("utf-8", {
          fatal: true,
        }).decode(bytes);
        if (!/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(base64Decoded)) {
          decoded = base64Decoded;
        }
      } catch {
        decoded = content;
      }
    }

    if (htmlMode === "full_html") {
      return decoded;
    }
    if (htmlMode === "sanitize") {
      return this.sanitizeHtml(decoded);
    }
    return this.htmlToText(decoded);
  }

  htmlToText(content) {
    const normalized = content
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/(?:p|div|li|h[1-6])\s*>/gi, "\n");
    const parsed = new DOMParser().parseFromString(normalized, "text/html");
    parsed
      .querySelectorAll("script, style, iframe, object, embed")
      .forEach((element) => element.remove());
    return (parsed.body.textContent || "").replace(/\n{3,}/g, "\n\n").trim();
  }

  sanitizeHtml(content) {
    const allowedTags = new Set([
      "A",
      "B",
      "BLOCKQUOTE",
      "BR",
      "DIV",
      "EM",
      "H1",
      "H2",
      "H3",
      "H4",
      "H5",
      "H6",
      "I",
      "LI",
      "OL",
      "P",
      "SPAN",
      "STRONG",
      "U",
      "UL",
    ]);
    const parsed = new DOMParser().parseFromString(content, "text/html");

    const sanitizeNode = (node: Node): void => {
      for (const child of Array.from(node.childNodes)) {
        if (!(child instanceof Element)) {
          continue;
        }

        const element: Element = child;
        if (
          ["SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED", "SVG", "MATH"].includes(
            element.tagName
          )
        ) {
          element.remove();
          continue;
        }

        sanitizeNode(element);
        if (!allowedTags.has(element.tagName)) {
          element.replaceWith(...Array.from(element.childNodes));
          continue;
        }

        const href =
          element.tagName === "A" ? element.getAttribute("href") : null;
        for (const attribute of Array.from(element.attributes)) {
          element.removeAttribute(attribute.name);
        }

        if (href && element.tagName === "A") {
          try {
            const url = new URL(href, document.baseURI);
            if (["http:", "https:", "mailto:"].includes(url.protocol)) {
              element.setAttribute("href", url.href);
              element.setAttribute("rel", "noopener noreferrer");
              element.setAttribute("target", "_blank");
            }
          } catch {
            // Invalid URLs are left as non-clickable link text.
          }
        }
      }
    };

    sanitizeNode(parsed.body);
    return parsed.body.innerHTML;
  }

  getWorkspaceAttributes() {
    const attributes =
      this.hass.states[this.config.entity]?.attributes || {};
    if (!attributes.stored_in_store || !attributes.store_key) {
      return attributes;
    }

    const storeKey = attributes.store_key;
    if (this._storedData?.[storeKey]) {
      return this._storedData[storeKey];
    }

    if (!this._fetchingKeys?.[storeKey] && !this._storeErrors?.[storeKey]) {
      this._fetchingKeys = { ...(this._fetchingKeys || {}), [storeKey]: true };

      this.hass.callWS({
        type: "ecole_directe/get_stored_data",
        key: storeKey,
      }).then((response) => {
          if (!response.data || typeof response.data !== "object") {
            throw new Error(`No stored workspace data found for ${storeKey}`);
          }
          this._storedData = {
            ...(this._storedData || {}),
            [storeKey]: response.data,
          };
          this.requestUpdate();
        })
        .catch((error) => {
          console.error("Error fetching stored workspace data", storeKey, error);
          this._storeErrors = {
            ...(this._storeErrors || {}),
            [storeKey]: true,
          };
          this.requestUpdate();
        })
        .finally(() => {
          const fetchingKeys = { ...(this._fetchingKeys || {}) };
          delete fetchingKeys[storeKey];
          this._fetchingKeys = fetchingKeys;
        });
    }

    return null;
  }

  getWorkspaceContentOrLoading() {
    const stateAttributes =
      this.hass.states[this.config.entity]?.attributes || {};
    const attributes = this.getWorkspaceAttributes();
    if (attributes) {
      return { attributes };
    }

    const storeKey = stateAttributes.store_key;
    return {
      loading: html`<div class="ed-card-no-data">
        ${this._storeErrors?.[storeKey]
          ? "Impossible de charger les données de l'espace de travail"
          : "Chargement des données de l'espace de travail..."}
      </div>`,
    };
  }

  getCardHeader() {
    const attributes = this.getWorkspaceAttributes();
    const workspace = attributes?.["Espace de travail"];
    const title = this.getFirstValue(workspace, ["titre", "nom"]);

    return html`<div class="workspace-header">
      ${title ? `Espace de travail : ${title}` : "Espace de travail"}
    </div>`;
  }

  getLatestItems(items, limit) {
    if (!Array.isArray(items)) {
      return [];
    }

    return items
      .map((item, index) => ({
        item,
        index,
        timestamp: this.getTimestamp(item),
      }))
      .sort((first, second) => {
        if (first.timestamp !== null && second.timestamp !== null) {
          return second.timestamp - first.timestamp;
        }
        if (first.timestamp !== null) {
          return -1;
        }
        if (second.timestamp !== null) {
          return 1;
        }
        return first.index - second.index;
      })
      .slice(0, limit)
      .map(({ item }) => item);
  }

  getLimit(value, fallback) {
    const limit = Number(value ?? fallback);
    return Number.isFinite(limit) ? Math.max(0, Math.floor(limit)) : fallback;
  }

  getTimestamp(item) {
    const value = this.getFirstValue(item, ["creeLe", "date"]);
    if (value === null) {
      return null;
    }

    if (typeof value === "number") {
      return value < 1000000000000 ? value * 1000 : value;
    }

    const frenchDate = String(value).match(
      /^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+à\s+(\d{1,2}):(\d{2}))?/
    );
    const timestamp = frenchDate
      ? new Date(
          Number(frenchDate[3]),
          Number(frenchDate[2]) - 1,
          Number(frenchDate[1]),
          Number(frenchDate[4] || 0),
          Number(frenchDate[5] || 0)
        ).getTime()
      : Date.parse(String(value));

    return Number.isNaN(timestamp) ? null : timestamp;
  }

  getFirstValue(item, keys) {
    if (!item || typeof item !== "object") {
      return null;
    }

    for (const key of keys) {
      const value = item[key];
      if (
        value !== null &&
        value !== undefined &&
        typeof value !== "object" &&
        String(value).trim() !== ""
      ) {
        return value;
      }
    }
    return null;
  }

  getItem(item) {
    const rawContent = this.getFirstValue(item, [
      "resume",
      "descriptif",
      "contenu",
      "texte",
      "message",
      "description",
      "commentaire",
    ]);
    const content =
      typeof rawContent === "string"
        ? this.decodeContent(rawContent, this.getHtmlMode())
        : rawContent;
    const htmlMode = this.getHtmlMode();
    const date = this.getFirstValue(item, ["creeLe", "date"]);
    const cloudDetails = this.getCloudDetails(item);

    return html`<article><hr />
      ${content
        ? html`<div class="item-content">
            ${htmlMode === "text" ? content : unsafeHTML(content)}
          </div>`
        : ""}
      ${cloudDetails.map(
        (detail) => html`<div class="cloud-details">
          ${detail.action
            ? html`Action : ${detail.action}<br />`
            : ""}
          ${detail.unc ? html`Chemin : ${detail.unc}` : ""}
        </div>`
      )}
      ${date ? html`<div class="item-date">${date}</div>` : ""}
    </article>`;
  }

  getCloudDetails(item) {
    const response = item?.cloud_details;
    if (!response || typeof response !== "object") {
      return [];
    }

    const data = Array.isArray(response)
      ? response
      : Array.isArray(response.data)
        ? response.data
        : response.data && typeof response.data === "object"
          ? [response.data]
          : "action" in response || "unc" in response
            ? [response]
            : [];

    return data
      .filter(
        (detail) =>
          detail &&
          typeof detail === "object" &&
          (detail.action || detail.unc)
      )
      .map((detail) => ({
        action: CLOUD_ACTION_LABELS[detail.action] || detail.action,
        unc: detail.unc,
      }));
  }

  static get styles() {
    return css`
      ${super.styles}
      section {
        padding: 0 12px 12px;
      }
      .item-content {
        padding-top: 4px;
        font-weight: normal;
        overflow-wrap: anywhere;
      }
      .cloud-details {
        padding-top: 4px;
        overflow-wrap: anywhere;
      }
      .item-date,
      .empty {
        padding-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.9em;
        font-weight: normal;
      }
      .workspace-header {
        padding: 12px;
        text-align: center;
        font-weight: bold;
        font-size: 1em;
      }
    `;
  }
}

export default EDWorkspaceCard;
