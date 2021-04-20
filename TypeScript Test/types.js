import { templateSub } from "./string_template.js";
class Sidebar {
    constructor(title, rounds) {
        this.title = title;
        this.rounds = rounds;
    }
    renderToHtmlString(roundNumber, roundSection, questionNumber) {
        const round = this.rounds[roundNumber];
        const question = questionNumber !== undefined ? round[questionNumber] : "divider";
        return `${this.title} ${round} ${roundSection} ${question}`;
    }
}
class SlideType {
    constructor(sidebar) {
        this.sidebar = sidebar;
    }
    renderHtmlWithSidebar(roundNumber, roundSection, questionNumber) {
        const htmlTemplate = `
		<div>
			<div class="slide-with-sidebar main-content">$mainContent</div>
			$maybeSidebar
		</div>`;
        return templateSub(htmlTemplate, {
            maybeSidebar: this.sidebar !== undefined
                ? this.sidebar.renderToHtmlString(roundNumber, roundSection, questionNumber)
                : "",
        });
    }
}
export class FreeformSlide extends SlideType {
    constructor(html, sidebar) {
        super(sidebar);
        this.html = html;
    }
    renderToHtmlString() {
        return this.html + 1;
    }
}
class DividerSlide extends SlideType {
    constructor({ title, subtitle, admonition, addtlHtml, sidebar, }) {
        super(sidebar);
        this.title = title;
        this.subtitle = subtitle;
        this.admonition = admonition;
        this.addtlHtml = addtlHtml !== null && addtlHtml !== void 0 ? addtlHtml : "";
    }
    renderToHtmlString() {
        throw new Error("Method not implemented.");
    }
}
export class PreQuestionsSlide extends DividerSlide {
    // roundNumber: number;
    // title: string;
    // addtlHtml: string;
    constructor({ roundNumber, roundTitle, addtlHtml, sidebar, }) {
        super({
            title: `Round ${roundNumber}`,
            subtitle: `${roundTitle}`,
            admonition: "Please mute yourselves!",
            addtlHtml,
            sidebar,
        });
        // this.roundNumber = roundNumber;
        // this.title = roundTitle;
        // this.addtlHtml = addtlHtml ?? "";
    }
    renderToHtmlString() {
        throw new Error("Method not implemented.");
    }
}
export class PreAnswersSlide extends DividerSlide {
    // roundNumber: number;
    // title: string;
    // addtlHtml: string;
    constructor({ roundNumber, roundTitle, addtlHtml, sidebar, }) {
        super({
            title: `Round ${roundNumber}`,
            subtitle: `${roundTitle}`,
            admonition: "Please mute yourselves!",
            addtlHtml,
            sidebar,
        });
        // this.roundNumber = roundNumber;
        // this.title = roundTitle;
        // this.addtlHtml = addtlHtml ?? "";
    }
    renderToHtmlString() {
        throw new Error("Method not implemented.");
    }
}
class QuestionOrAnswerSlide extends SlideType {
    constructor({ roundNumber, roundTitle, questionNumber, question, answer, slideLayout, sidebar, }) {
        super(sidebar);
        this.roundNumber = roundNumber;
        this.roundTitle = roundTitle;
        this.questionNumber = questionNumber;
        this.question = question;
        this.answer = answer;
        this.slideLayout = slideLayout !== null && slideLayout !== void 0 ? slideLayout : 0 /* noMedia */;
    }
    renderToHtmlString() {
        throw new Error("Method not implemented.");
    }
}
export class QuestionSlide extends QuestionOrAnswerSlide {
    constructor({ roundNumber, roundTitle, questionNumber, question, slideLayout, sidebar, }) {
        super({
            roundNumber,
            roundTitle,
            questionNumber,
            question,
            answer: undefined,
            slideLayout,
            sidebar,
        });
    }
}
export class AnswerSlide extends QuestionOrAnswerSlide {
    constructor({ roundNumber, roundTitle, questionNumber, question, answer, slideLayout, sidebar, }) {
        super({
            roundNumber,
            roundTitle,
            questionNumber,
            question,
            answer,
            slideLayout,
            sidebar,
        });
    }
}
