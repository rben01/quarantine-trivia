export type TriviaItem = {
	question: string;
	answer: string;
	section: string;
	topic: string;
	question_image: string;
	answer_image: string;
	answer_image_is_full_height: string;
};

type QuestionMediaFormat =
	| "noMedia"
	| "mediaInQuestion"
	| "mediaInAnswer"
	| "separateMediaInQAndA"
	| "fullHeightMediaInQAndA"
	| "fullHeightMediaInQuestionOnly"
	| "fullHeightMediaInAnswerOnly";

type SlideLayout =
	| "noMedia"
	| "mediaInQuestion"
	| "mediaInAnswer"
	| "mediasInQuestionAndAnswer"
	| "fullHeightMedia";

type SlideNodeTree = {
	slideRootNode: HTMLElement;
	sidebarNode?: HTMLElement;
	mainContentNode?: HTMLElement;
	qaNode?: HTMLElement;
	questionNode?: HTMLElement;
	answerNode?: HTMLElement;
	questionMediaNode?: HTMLElement;
	answerMediaNode?: HTMLElement;
	tallMediaNode?: HTMLElement;
};

const enum RoundSection {
	preQuestions,
	questions,
	preAnswers,
	answers,
	other,
}

interface HtmlRenderable {
	renderToNode(
		roundNumber: number,
		roundSection: RoundSection,
		questionNumber?: number,
	): SlideNodeTree;
}

class Sidebar {
	title: string;
	rounds: string[][];

	constructor(title: string, rounds: string[][]) {
		this.title = title;
		this.rounds = rounds;
	}

	renderToNode(
		roundNumber: number,
		roundSection: RoundSection,
		questionNumber?: number,
	): HTMLElement {
		const round = this.rounds[roundNumber];
		const question =
			questionNumber !== undefined ? round[questionNumber] : "divider";
		const node = document.createElement("div");
		const text = document.createTextNode(
			`${this.title} ${round} ${roundSection} ${question}`,
		);
		node.appendChild(text);

		return node;
	}
}

abstract class SlideType implements HtmlRenderable {
	sidebar?: Sidebar;

	constructor(sidebar?: Sidebar) {
		this.sidebar = sidebar;
	}

	renderToNode(
		roundNumber: number,
		roundSection: RoundSection,
		questionNumber?: number,
	): SlideNodeTree {
		const slide = document.createElement("div");
		const mainContentNode = document.createElement("div");
		slide.appendChild(mainContentNode);
		mainContentNode.classList.add("main-content");

		const nodes: SlideNodeTree = { slideRootNode: slide, mainContentNode };

		if (this.sidebar === undefined) {
			slide.classList.add("no-sidebar");
		} else {
			slide.classList.add("has-sidebar");

			const sidebarNode = this.sidebar.renderToNode(
				roundNumber,
				roundSection,
				questionNumber,
			);
			slide.appendChild(sidebarNode);

			nodes.sidebarNode = sidebarNode;
		}

		return nodes;
	}
}

export class FreeformSlide extends SlideType {
	html: string;

	constructor(html: string, sidebar?: Sidebar) {
		super(sidebar);
		this.html = html;
	}

	renderToNode(
		roundNumber: number,
		roundSection: RoundSection,
		questionNumber?: number,
	): SlideNodeTree {
		const nodes = super.renderToNode(roundNumber, roundSection, questionNumber);
		const newNode = document.createElement("div");
		newNode.innerHTML = this.html;
		nodes.mainContentNode?.appendChild(newNode);
		return nodes;
	}
}

abstract class DividerSlide extends SlideType {
	title: string;
	subtitle: string;
	admonition: string;
	addtlHtml: string;
	sidebar?: Sidebar;

	constructor({
		title,
		subtitle,
		admonition,
		addtlHtml,
		sidebar,
	}: {
		title: string;
		subtitle: string;
		admonition: string;
		addtlHtml?: string;
		sidebar?: Sidebar;
	}) {
		super(sidebar);
		this.title = title;
		this.subtitle = subtitle;
		this.admonition = admonition;
		this.addtlHtml = addtlHtml ?? "";
	}

	renderToNode(
		roundNumber: number,
		roundSection: RoundSection,
		questionNumber?: number,
	): SlideNodeTree {
		const nodes = super.renderToNode(roundNumber, roundSection, questionNumber);
		const content = document.createElement("div");
		content.classList.add("divider-slider");
		nodes.mainContentNode?.append(content);

		const titleContainer = document.createElement("div");
		titleContainer.classList.add("title-container");
		content.appendChild(titleContainer);

		const title = document.createElement("div");
		title.classList.add("title");
		title.append(this.title);
		titleContainer.appendChild(title);

		const subtitle = document.createElement("div");
		subtitle.classList.add("subtitle");
		subtitle.append(this.subtitle);
		titleContainer.appendChild(subtitle);

		const admonition = document.createElement("div");
		admonition.classList.add("admonition");
		admonition.append(this.admonition);
		content.append(admonition);

		if (this.addtlHtml !== undefined) {
			const addtHtml = document.createElement("div");
			addtHtml.innerHTML = this.addtlHtml;
			content.append(addtHtml);
		}

		return nodes;
	}
}

export class PreQuestionsSlide extends DividerSlide {
	constructor({
		roundNumber,
		roundTitle,
		addtlHtml,
		sidebar,
	}: {
		roundNumber: number;
		roundTitle: string;
		addtlHtml?: string;
		sidebar?: Sidebar;
	}) {
		super({
			title: `Round ${roundNumber}`,
			subtitle: `${roundTitle}`,
			admonition: "Please mute yourselves!",
			addtlHtml,
			sidebar,
		});
	}
}

export class PreAnswersSlide extends DividerSlide {
	constructor({
		roundNumber,
		roundTitle,
		addtlHtml,
		sidebar,
	}: {
		roundNumber: number;
		roundTitle: string;
		addtlHtml?: string;
		sidebar?: Sidebar;
	}) {
		super({
			title: `Round ${roundNumber}`,
			subtitle: `${roundTitle}`,
			admonition: "Please mute yourselves!",
			addtlHtml,
			sidebar,
		});
	}
}

abstract class QuestionOrAnswerSlide extends SlideType {
	roundNumber: number;
	roundTitle: string;
	questionNumber: number;
	question: string;
	answer?: string;
	slideLayout: SlideLayout;
	media1?: string;
	media2?: string;
	sidebar?: Sidebar;

	constructor({
		roundNumber,
		roundTitle,
		questionNumber,
		question,
		answer,
		slideLayout,
		questionImage,
		answerImage,
		sidebar,
	}: {
		roundNumber: number;
		roundTitle: string;
		questionNumber: number;
		question: string;
		answer?: string;
		slideLayout?: SlideLayout;
		questionImage?: string;
		answerImage?: string;
		sidebar?: Sidebar;
	}) {
		super(sidebar);
		this.roundNumber = roundNumber;
		this.roundTitle = roundTitle;
		this.questionNumber = questionNumber;
		this.question = question;
		this.answer = answer;
		this.slideLayout = slideLayout ?? "noMedia";
	}

	renderToNode(
		roundNumber: number,
		roundSection: RoundSection,
		questionNumber?: number,
	): SlideNodeTree {
		const nodes = super.renderToNode(roundNumber, roundSection, questionNumber);

		const content = document.createElement("div");
		nodes.mainContentNode?.appendChild(content);

		const qaContainer = document.createElement("div");
		qaContainer.classList.add("qa-container");
		content.appendChild(qaContainer);

		const questionNode = document.createElement("div");
		questionNode.classList.add("question-container");
		qaContainer.appendChild(questionNode);

		const questionBodyNode = document.createElement("div");
		questionBodyNode.classList.add("question-body");
		questionNode.appendChild(questionBodyNode);

		const answerNode = this.answer ?? false ? document.createElement("div") : null;
		const answerBodyNode =
			this.answer ?? false ? document.createElement("div") : null;
		if (answerNode !== null && answerBodyNode !== null) {
			answerNode.classList.add("answer-container");
			qaContainer.appendChild(answerNode);

			answerBodyNode.classList.add("answer-body");
			answerNode.appendChild(answerBodyNode);
		}

		const mediaContainer1 =
			this.media1 ?? false ? document.createElement("div") : null;
		const mediaContainer2 =
			this.media2 ?? false ? document.createElement("div") : null;

		switch (this.slideLayout) {
			case "noMedia":
				break;
			case "fullHeightMedia": {
				const img = document.createElement("img");
				img.classList.add("media1 full-height-media");
				mediaContainer1?.appendChild(img);

				content.appendChild(mediaContainer1 as HTMLElement);
				break;
			}
			case "mediaInQuestion":
				const img = document.createElement("img");
				img.classList.add("media1 full-height-media");
				mediaContainer1?.appendChild(img);

				content.appendChild(mediaContainer1 as HTMLElement);
				questionNode.appendChild(mediaContainer1);
				break;
			case "mediaInAnswer":
				answerNode?.appendChild(mediaContainer1);
		}

		return nodes;
	}
	// renderToHtmlString(
	// 	roundNumber: number,
	// 	roundSection: RoundSection,
	// 	questionNumber?: number,
	// ): string {
	// 	const slideTemplateHtml = this.renderHtmlWithSidebar(
	// 		roundNumber,
	// 		roundSection,
	// 		questionNumber,
	// 	);

	// 		const mainContent = this.slideLayout==='fullHeightMedia'? templateSub(slideTemplateHtml, {mainHtml:`<div class="media-full-height"><div></div></div>`})

	// 	if (this.slideLayout === 'fullHeightMedia')
	// 	switch (this.slideLayout) {
	// 		case "noMedia":
	// 			console.log(1);
	// 			break;
	// 		default:
	// 			throw new Error(`Unknown slide layout ${this.slideLayout}`);
	// 	}
	// 	const mainHtml = `
	// 		<div class="question-answer">
	// 		$questionHtml
	// 		$answerHtml
	// 		</div>`;
	// }
}

export class QuestionSlide extends QuestionOrAnswerSlide {
	constructor({
		roundNumber,
		roundTitle,
		questionNumber,
		question,
		slideLayout,
		sidebar,
	}: {
		roundNumber: number;
		roundTitle: string;
		questionNumber: number;
		question: string;
		slideLayout?: SlideLayout;
		sidebar?: Sidebar;
	}) {
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
	constructor({
		roundNumber,
		roundTitle,
		questionNumber,
		question,
		answer,
		slideLayout,
		sidebar,
	}: {
		roundNumber: number;
		roundTitle: string;
		questionNumber: number;
		question: string;
		answer: string;
		slideLayout?: SlideLayout;
		sidebar?: Sidebar;
	}) {
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
