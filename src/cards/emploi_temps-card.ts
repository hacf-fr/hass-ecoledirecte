import BaseEDCard from "./base-card";

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

function isSameDay(d1, d2) {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

class EDTimetableCard extends BaseEDCard {
  lunchBreakRendered = false;

  initCard() {}

  getEndedLessonsMode(): "none" | "dim" | "hide" {
    const val = this.config.ended_lessons;
    if (
      val === "hide" ||
      val === "hidden" ||
      val === "cache" ||
      val === "caché"
    ) {
      return "hide";
    }
    if (val === "dim") {
      return "dim";
    }
    if (val === "none" || val === "normal") {
      return "none";
    }
    // Backwards compatibility with old booleans
    if (this.config.hide_ended_lessons || this.config.hide_past_lessons) {
      return "hide";
    }
    if (this.config.dim_ended_lessons === false) {
      return "none";
    }
    return "dim";
  }

  getBreakRow(label, ended) {
    return html` <tr class="lunch-break ${ended ? "lesson-ended" : ""}">
      <td></td>
      <td><span></span></td>
      <td colspan="2">
        <span class="lesson-name">${label}</span>
      </td>
    </tr>`;
  }

  getTimetableRow(lesson) {
    let currentDate = new Date().getTime();
    let startAt = Date.parse(lesson.start_at);
    let endAt = Date.parse(lesson.end_at);

    const mode = this.getEndedLessonsMode();
    const isHideEnded = mode === "hide";
    const isDimEnded = mode === "dim";

    let prefix = html``;
    if (
      this.config.display_lunch_break &&
      lesson.is_afternoon &&
      !this.lunchBreakRendered
    ) {
      const lunchEnded = startAt < currentDate;
      if (!(isHideEnded && lunchEnded)) {
        prefix = this.getBreakRow(
          "Repas",
          isDimEnded && lunchEnded
        );
      }
      this.lunchBreakRendered = true;
    }

    let content = html`
      <tr
        class="${lesson.is_annule ? "lesson-canceled" : lesson.is_modifie ? "lesson-modified" : ""} ${isDimEnded && endAt < currentDate
          ? "lesson-ended"
          : ""}"
      >
        <td>
          ${lesson.start_time}<br />
          ${lesson.end_time}
        </td>
        <td>
          <span style="background-color:${lesson.background_color}"></span>
        </td>
        <td>
          <span class="lesson-name">
            ${lesson.lesson}${lesson.remplace
              ? html`<span class="lesson-replaced"> (remplace ${lesson.remplace})</span>`
              : ""}
            ${lesson.is_modifie
              ? html`<span class="lesson-modified-dot"></span>`
              : ""}
          </span>
          ${this.config.display_classroom
            ? html`<span class="lesson-classroom">
                ${lesson.salle ? "Salle " + lesson.salle : ""}
                ${lesson.salle && this.config.display_teacher ? ", " : ""}
              </span>`
            : ""}
          ${this.config.display_teacher
            ? html`<span class="lesson-teacher"> ${lesson.prof} </span>`
            : ""}
        </td>
        <td>
          ${lesson.dispense
            ? html`<span class="lesson-status">${lesson.dispense}</span>`
            : ""}
        </td>
      </tr>
    `;
    return html`${prefix}${content}`;
  }

  getFormattedDate(lesson) {
    return new Date(lesson.start_at)
      .toLocaleDateString("fr-FR", {
        weekday: "long",
        day: "2-digit",
        month: "2-digit",
      })
      .replace(/^(.)/, (match) => match.toUpperCase());
  }

  getFormattedTime(time) {
    return new Intl.DateTimeFormat("fr-FR", {
      hour: "numeric",
      minute: "numeric",
    }).format(new Date(time));
  }

  getDayHeader(firstLesson, dayStartAt, dayEndAt, daysCount, isLastDay = false) {
    return html`<div class="ed-timetable-header">
      ${this.config.enable_slider
        ? html`<span
            class="ed-timetable-header-arrow-left ${daysCount === 0
              ? "disabled"
              : ""}"
            @click=${(e) => this.changeDay("previous", e)}
            >←</span
          >`
        : ""}
      <span class="ed-timetable-header-date"
        >${this.getFormattedDate(firstLesson)}</span
      >
      ${this.config.display_day_hours && dayStartAt && dayEndAt
        ? html`<span class="ed-timetable-header-hours">
            ${this.getFormattedTime(dayStartAt)} -
            ${this.getFormattedTime(dayEndAt)}
          </span>`
        : ""}
      ${this.config.enable_slider
        ? html`<span
            class="ed-timetable-header-arrow-right ${isLastDay
              ? "disabled"
              : ""}"
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
        "ed-timetable-day-wrapper"
      );
    let hasNextDay =
      activeDay.nextElementSibling &&
      activeDay.nextElementSibling.classList.contains(
        "ed-timetable-day-wrapper"
      );
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
          "ed-timetable-day-wrapper"
        );
      hasNextDay =
        newActiveDay.nextElementSibling &&
        newActiveDay.nextElementSibling.classList.contains(
          "ed-timetable-day-wrapper"
        );

      newActiveDay
        .querySelector(".ed-timetable-header-arrow-left")
        ?.classList.toggle("disabled", !hasPreviousDay);

      newActiveDay
        .querySelector(".ed-timetable-header-arrow-right")
        ?.classList.toggle("disabled", !hasNextDay);
    }
  }

  findRelatedWeekEntity(
    baseEntityId: string,
    targetWeekKey: string,
    targetSuffix: string
  ): string | null {
    if (!baseEntityId) {
      return null;
    }

    const weekKeywords = [
      "semaine_en_cours",
      "semaine_suivante",
      "semaine_apres_suivante",
      "aujourd_hui",
      "demain",
      "jour_suivant",
    ];

    let candidateByKeyword: string | null = null;
    for (const kw of weekKeywords) {
      if (baseEntityId.includes(kw)) {
        const candidate = baseEntityId.replace(kw, targetWeekKey);
        if (this.hass?.states?.[candidate]) {
          return candidate;
        }
        if (!candidateByKeyword) {
          candidateByKeyword = candidate;
        }
        break;
      }
    }

    const suffixMatches = ["_1", "_2", "_3", "_today", "_tomorrow", "_next_day"];
    let candidateBySuffix: string | null = null;
    for (const suf of suffixMatches) {
      if (baseEntityId.endsWith(suf)) {
        const candidate = baseEntityId.slice(0, -suf.length) + targetSuffix;
        if (this.hass?.states?.[candidate]) {
          return candidate;
        }
        if (!candidateBySuffix) {
          candidateBySuffix = candidate;
        }
        break;
      }
    }

    if (this.hass?.states) {
      const baseState = this.hass.states[baseEntityId];
      const childFirstname = baseState?.attributes?.prenom;

      for (const entityId of Object.keys(this.hass.states)) {
        if (entityId.startsWith("sensor.") && entityId.includes(targetWeekKey)) {
          const stateObj = this.hass.states[entityId];
          if (childFirstname && stateObj?.attributes?.prenom === childFirstname) {
            return entityId;
          }
        }
      }

      for (const entityId of Object.keys(this.hass.states)) {
        if (
          entityId.startsWith("sensor.") &&
          (entityId.endsWith(targetSuffix) ||
            entityId.includes(`timetable${targetSuffix}`))
        ) {
          const stateObj = this.hass.states[entityId];
          if (childFirstname && stateObj?.attributes?.prenom === childFirstname) {
            return entityId;
          }
        }
      }
    }

    return candidateByKeyword || candidateBySuffix;
  }

  getEntities(): string[] {
    if (
      this.config.entities &&
      Array.isArray(this.config.entities) &&
      this.config.entities.length > 0
    ) {
      return this.config.entities;
    }

    const baseEntity = this.config.entity;
    if (!baseEntity) {
      return [];
    }

    const entities: string[] = [baseEntity];

    if (Array.isArray(this.config.display_weeks)) {
      for (const w of this.config.display_weeks) {
        if (typeof w === "string") {
          if (w.startsWith("sensor.")) {
            if (!entities.includes(w)) entities.push(w);
          } else if (
            w.includes("suivante") &&
            !w.includes("apres") &&
            !w.includes("après")
          ) {
            const nextEntity = this.findRelatedWeekEntity(
              baseEntity,
              "semaine_suivante",
              "_2"
            );
            if (nextEntity && !entities.includes(nextEntity)) {
              entities.push(nextEntity);
            }
          } else if (w.includes("apres") || w.includes("après")) {
            const afterEntity = this.findRelatedWeekEntity(
              baseEntity,
              "semaine_apres_suivante",
              "_3"
            );
            if (afterEntity && !entities.includes(afterEntity)) {
              entities.push(afterEntity);
            }
          }
        }
      }
    }

    const showWeeksNum = Number(
      this.config.show_weeks || this.config.weeks || 0
    );

    const showNext =
      this.config.display_next_week === true || showWeeksNum >= 2;

    const showWeekAfterNext =
      this.config.display_week_after_next === true || showWeeksNum >= 3;

    if (showNext) {
      const nextEntity = this.findRelatedWeekEntity(
        baseEntity,
        "semaine_suivante",
        "_2"
      );
      if (nextEntity && !entities.includes(nextEntity)) {
        entities.push(nextEntity);
      }
    }

    if (showWeekAfterNext) {
      const afterNextEntity = this.findRelatedWeekEntity(
        baseEntity,
        "semaine_apres_suivante",
        "_3"
      );
      if (afterNextEntity && !entities.includes(afterNextEntity)) {
        entities.push(afterNextEntity);
      }
    }

    return entities;
  }

  getCardHeader() {
    const entity =
      this.config.entity ||
      (this.config.entities && this.config.entities[0]);
    if (entity && this.hass?.states?.[entity]) {
      const child_attributes = this.hass.states[entity].attributes;
      if (child_attributes) {
        const child_name =
          typeof child_attributes["prenom"] === "string" &&
          child_attributes["prenom"].length > 0
            ? child_attributes["prenom"]
            : child_attributes["nom_complet"];
        return html`<div class="ed-card-header">
          ${this.header_title} ${child_name}
        </div>`;
      }
    }
    return super.getCardHeader();
  }

  // we override the render method to return the card content
  render() {
    if (!this.config || !this.hass) {
      return html`<div class="ed-card-no-data">
        Veuillez configurer la carte
      </div>`;
    }

    const entities = this.getEntities();
    if (entities.length === 0) {
      return html`<div class="ed-card-no-data">
        Veuillez choisir une autre entité
      </div>`;
    }

    let allLessons: any[] = [];
    let isFetching = false;
    let foundValidEntity = false;

    for (const entityId of entities) {
      const stateObj = this.hass.states[entityId];
      if (!stateObj) {
        continue;
      }
      foundValidEntity = true;
      let lessons = stateObj.attributes["Emploi du temps"];
      if (!lessons || !Array.isArray(lessons)) {
        continue;
      }

      if (lessons.length > 0 && lessons[0]?.stored_in_store) {
        const storeKey = lessons[0].store_key;
        if (this._storedData && this._storedData[storeKey]) {
          lessons = this._storedData[storeKey];
        } else {
          isFetching = true;
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
                console.error(
                  "Error fetching stored data for key",
                  storeKey,
                  err
                );
              });
          }
        }
      }

      if (Array.isArray(lessons) && !lessons[0]?.stored_in_store) {
        allLessons.push(...lessons);
      }
    }

    if (isFetching) {
      return html`<div class="ed-card-no-data">
        Chargement de l'emploi du temps...
      </div>`;
    }

    if (!foundValidEntity) {
      return html`<div class="ed-card-no-data">
        Veuillez choisir une autre entité
      </div>`;
    }

    if (allLessons.length === 0) {
      return html` <ha-card
        id="${this.config.entity}-card"
        class="${this.config.enable_slider ? "ed-timetable-card-slider" : ""}"
      >
        ${this.config.display_header ? this.getCardHeader() : ""}
        <div class="ed-card-no-data">${this.no_data_message}</div>
      </ha-card>`;
    }

    // Deduplicate lessons
    const lessons: any[] = [];
    const seen = new Set<string>();
    for (const l of allLessons) {
      if (!l || !l.start_at) continue;
      const key = `${l.start_at}_${l.end_at}_${l.lesson || ""}_${l.groupe_id || ""}`;
      if (!seen.has(key)) {
        seen.add(key);
        lessons.push(l);
      }
    }

    // Sort chronologically
    lessons.sort((a, b) => {
      const timeA = new Date(a.start_at).getTime();
      const timeB = new Date(b.start_at).getTime();
      return timeA - timeB;
    });

    const mode = this.getEndedLessonsMode();
    const isHideEnded = mode === "hide";
    const isDimEnded = mode === "dim";

    let displayLessons = lessons;
    if (isHideEnded) {
      const nowMs = Date.now();
      displayLessons = lessons.filter((l) => Date.parse(l.end_at) > nowMs);
    }

    if (displayLessons.length === 0) {
      return html` <ha-card
        id="${this.config.entity}-card"
        class="${this.config.enable_slider ? "ed-timetable-card-slider" : ""}"
      >
        ${this.config.display_header ? this.getCardHeader() : ""}
        <div class="ed-card-no-data">${this.no_data_message}</div>
      </ha-card>`;
    }

    // Group lessons into days
    const days: any[][] = [];
    let currentDayLessons: any[] = [];

    for (let index = 0; index < displayLessons.length; index++) {
      const lesson = displayLessons[index];
      if (lesson.isAnnule && index < displayLessons.length - 1) {
        const nextLesson = displayLessons[index + 1];
        if (lesson.start_at === nextLesson.start_at && !nextLesson.isAnnule) {
          continue;
        }
      }
      currentDayLessons.push(lesson);

      const currentFormattedDate = this.getFormattedDate(lesson);
      const nextLesson =
        index + 1 < displayLessons.length ? displayLessons[index + 1] : null;
      const nextFormattedDate = nextLesson
        ? this.getFormattedDate(nextLesson)
        : null;

      if (!nextLesson || currentFormattedDate !== nextFormattedDate) {
        if (currentDayLessons.length > 0) {
          days.push(currentDayLessons);
          currentDayLessons = [];
        }
      }
    }

    // Determine active day for slider
    let activeDay = 0;
    if (this.config.enable_slider) {
      const now = new Date();
      let todayIndex = -1;
      for (let d = 0; d < days.length; d++) {
        const dayLessons = days[d];
        const lastLesson = dayLessons[dayLessons.length - 1];
        const endOfDay = new Date(lastLesson.end_at);
        if (isSameDay(endOfDay, now)) {
          todayIndex = d;
          if (this.config.switch_to_next_day && endOfDay < now) {
            activeDay = Math.min(d + 1, days.length - 1);
          } else {
            activeDay = d;
          }
          break;
        }
      }
      if (todayIndex === -1 && this.config.switch_to_next_day) {
        for (let d = 0; d < days.length; d++) {
          const dayLessons = days[d];
          const lastLesson = dayLessons[dayLessons.length - 1];
          const endOfDay = new Date(lastLesson.end_at);
          if (endOfDay >= now) {
            activeDay = d;
            break;
          }
        }
      }
    }

    const itemTemplates = [];
    for (let daysCount = 0; daysCount < days.length; daysCount++) {
      const dayLessons = days[daysCount];
      this.lunchBreakRendered = false;

      let dayStartAt = null;
      let dayEndAt = null;
      for (const l of dayLessons) {
        if (!l.isAnnule) {
          if (dayStartAt === null) {
            dayStartAt = l.start_at;
          }
          dayEndAt = l.end_at;
        }
      }
      if (dayStartAt === null && dayLessons.length > 0) {
        dayStartAt = dayLessons[0].start_at;
        dayEndAt = dayLessons[dayLessons.length - 1].end_at;
      }

      const dayTemplates = [];
      for (let lIdx = 0; lIdx < dayLessons.length; lIdx++) {
        const lesson = dayLessons[lIdx];
        dayTemplates.push(this.getTimetableRow(lesson));

        if (
          this.config.display_free_time_slots &&
          lIdx + 1 < dayLessons.length
        ) {
          const currentEndAt = new Date(lesson.end_at);
          const nextLesson = dayLessons[lIdx + 1];
          const nextLessonStartAt = new Date(nextLesson.start_at);
          if (
            lesson.is_morning === nextLesson.is_morning &&
            Math.floor(
              ((nextLessonStartAt as any) - (currentEndAt as any)) /
                1000 /
                60
            ) > 30
          ) {
            const now = new Date();
            const slotEnded = nextLessonStartAt < now;
            if (!(isHideEnded && slotEnded)) {
              dayTemplates.push(
                this.getBreakRow(
                  "Pas de cours",
                  isDimEnded && slotEnded
                )
              );
            }
          }
        }
      }

      const isLastDay = daysCount === days.length - 1;
      itemTemplates.push(html`
        <div
          class="${this.config.enable_slider
            ? "slider-enabled"
            : ""} ed-timetable-day-wrapper ${daysCount === activeDay
            ? "active"
            : ""}"
        >
          ${this.getDayHeader(
            dayLessons[0],
            dayStartAt,
            dayEndAt,
            daysCount,
            isLastDay
          )}
          <table>
            ${dayTemplates}
          </table>
        </div>
      `);
    }

    return html` <ha-card
      id="${this.config.entity}-card"
      class="${this.config.enable_slider ? "ed-timetable-card-slider" : ""}"
    >
      ${this.config.display_header ? this.getCardHeader() : ""}
      ${itemTemplates}
    </ha-card>`;
  }

  setConfig(config) {
    if (!config.entity && (!config.entities || config.entities.length === 0)) {
      throw new Error("Vous devez définir une entité");
    }

    const defaultConfig = {
      entity: null,
      entities: null,
      display_next_week: false,
      display_week_after_next: false,
      ended_lessons: "dim",
      display_header: true,
      display_classroom: true,
      display_teacher: true,
      display_day_hours: true,
      display_lunch_break: true,
      enable_slider: false,
      switch_to_next_day: false,
      display_free_time_slots: true,
    };

    this.config = {
      ...defaultConfig,
      ...config,
    };

    if (
      !this.config.entity &&
      Array.isArray(this.config.entities) &&
      this.config.entities.length > 0
    ) {
      this.config.entity = this.config.entities[0];
    }

    this.header_title = "Emploi du temps de ";
    this.no_data_message = "Pas d'emploi du temps à afficher";
  }

  static get styles() {
    return css`
      ${super.styles}
      .ed-timetable-card-slider .ed-timetable-day-wrapper {
        display: none;
      }
      .ed-timetable-card-slider .ed-timetable-day-wrapper.active {
        display: block;
      }
      .ed-timetable-card-slider .ed-timetable-header-date {
        display: inline-block;
        text-align: center;
        width: 120px;
      }
      .ed-timetable-header-arrow-left,
      .ed-timetable-header-arrow-right {
        cursor: pointer;
      }
      .ed-timetable-header-arrow-left.disabled,
      .ed-timetable-header-arrow-right.disabled {
        opacity: 0.3;
        pointer-events: none;
      }
      span.ed-timetable-header-hours {
        float: right;
      }
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
        width: 13%;
        text-align: right;
      }
      span.lesson-name {
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
      span.lesson-status {
        color: white;
        background-color: rgb(75, 197, 253);
        padding: 4px;
        border-radius: 4px;
      }
      .lesson-canceled span.lesson-name {
        text-decoration: line-through;
      }
      .lesson-canceled span.lesson-status {
        background-color: rgb(250, 50, 75);
      }
      .lesson-modified span.lesson-name {
        font-style: italic;
      }
      .lesson-modified-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: orange;
        margin-left: 6px;
        vertical-align: middle;
      }
      .lesson-replaced {
        font-size: 0.85em;
        font-style: italic;
        opacity: 0.7;
      }
      .lesson-ended {
        opacity: 0.3;
      }
      div:not(.slider-enabled).ed-timetable-day-wrapper
        + div:not(.slider-enabled).ed-timetable-day-wrapper {
        border-top: 1px solid white;
      }
    `;
  }

  static getStubConfig() {
    return {
      display_header: true,
      display_lunch_break: true,
      display_classroom: true,
      display_teacher: true,
      display_day_hours: true,
      ended_lessons: "dim",
      enable_slider: false,
      display_free_time_slots: true,
      switch_to_next_day: false,
      display_next_week: false,
      display_week_after_next: false,
    };
  }

  static getConfigElement() {
    return document.createElement("ecole_directe-emploi_temps-card-editor");
  }
}

customElements.define("ecole_directe-emploi_temps-card", EDTimetableCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ecole_directe-emploi_temps-card",
  name: "Carte de l'emploi du temps pour Ecole Directe",
  description: "Affiche l'emploi du temps pour Ecole Directe",
  documentationURL:
    "https://github.com/hacf-fr/EcoleDirecteHACards?tab=readme-ov-file#emploi_temps",
});
