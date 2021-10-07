import fitz
## PyMuPdf

MAX_X2 = 69
## All question numbers should have an x2 value less than this


class Question:
    """
    Attributes:
        question_number: int
            (Question number of the question)

        question_text: str
            (All the text belonging to the question)

        y1: float
            (Starting y value of the question)

        y2: float
            (End y value of the question)

        pixmap: fitz.Pixmap
            (Picture of the question as a fitz.Pixmap object)
    """

    def __init__(self, question_number: int, y1: float):
        self.question_number: int = question_number
        self.y1: float = y1

        self.y2: float = 0

        self.question_text: str = None
        self.bound: fitz.Rect = None
        self.page_number: int = None
        self.output_file: fitz.Document = fitz.open()

    def __repr__(self) -> str:
        return f"{self.question_number} from {self.y1} to {self.y2} on page {self.page_number + 1}"

    def set_other_props(self, page: fitz.Page):
        """
        Given a page object, set the question text, bounding rect, page_number
        and a fitz.Doc with one page cropped to the question's rect to output_file

        If y2 is not set, fails without error
        """

        if not self.y2:
            return

        self.bound = fitz.Rect(0, self.y1, 595, self.y2)
        self.page_number = page.number
        self.question_text = page.get_text(clip=self.bound)

        new_page = self.output_file.new_page(height=(self.y2 - self.y1))
        new_page.show_pdf_page(
            new_page.rect, page.parent, pno=self.page_number, clip=self.bound
        )


def __get_y2_if_valid_drawing(drawing) -> float:
    return drawing["rect"][3] if (drawing["rect"][2] - drawing["rect"][0] <= 498) else 0

    ## Ignore the long line separating the copyright text


def get_questions_from_page(page: fitz.Page):

    text_page: fitz.TextPage = page.getTextPage()

    textDict = text_page.extractDICT()
    lowermost_graphic_y2 = max(
        [
            0,
            *[__get_y2_if_valid_drawing(drawing) for drawing in page.get_drawings()],
            *[img["bbox"][3] for img in page.get_image_info()],
        ]
    )

    questions_on_this_page: list[Question] = []
    lowermost_text_y2 = 0

    try:
        BOLD_FONT_FOR_QUESTION_NUMBERS = textDict["blocks"][0]["lines"][0]["spans"][0][
            "font"
        ]

        ## Font used for question numbers is the same as that for page numbers, mostly just changes between documents, but checking each page for safety

    except:
        return []

    for block in textDict["blocks"][2:]:
        for line in block["lines"]:
            for span in line["spans"]:

                ## Assign span's y2 to lowest_text_y2 if it is below the current lowest text
                if (
                    span["text"].find("Space for working") == -1
                    and span["text"].strip() != ""
                ):
                    lowermost_text_y2 = max(lowermost_text_y2, span["bbox"][3])

                try:
                    qn = int(span["text"].strip())

                    if (
                        span["bbox"][2] < MAX_X2
                        and span["font"] == BOLD_FONT_FOR_QUESTION_NUMBERS
                    ):
                        try:
                            ## If there's a previous question on this page, then set that questions y2
                            questions_on_this_page[-1].y2 = span["bbox"][1] - 12
                            questions_on_this_page[-1].set_other_props(page)
                        except:
                            pass
                        finally:
                            questions_on_this_page.append(
                                Question(qn, span["bbox"][1] - 12)
                            )

                ## If conversion failed then it's not a question number
                except ValueError:
                    pass

    ##Compare the lowest drawing's y2 and the lowest text's y2 and set the last question's y2 to the max
    try:
        questions_on_this_page[-1].y2 = (
            max(lowermost_text_y2, lowermost_graphic_y2) + 12
        )
        questions_on_this_page[-1].set_other_props(page)

    except:
        pass
    finally:
        return questions_on_this_page


def get_questions_from_doc(document: fitz.Document, pages_to_skip: int = 0):
    questions_in_doc: list[Question] = []

    for page_index in range(pages_to_skip, len(document)):
        page = document[page_index]
        questions: list[Question] = get_questions_from_page(page)

        questions_in_doc.extend(questions)
    return questions_in_doc


def get_questions_from_filepath(filepath: str, pages_to_skip: int = 0):
    return get_questions_from_doc(fitz.open(filepath), pages_to_skip)


class SplitQuestionsDocument:
    def __init__(self, filepath: str, pages_to_skip: int) -> None:
        self.src: fitz.Document = fitz.open(filepath)
        self.questions: list[Question] = get_questions_from_doc(self.src, pages_to_skip)

    def get_questions_as_single_pdf(self):
        output: fitz.Document = fitz.open()

        for question in self.questions:
            page: fitz.Page = output.new_page(height=(question.y2 - question.y1))
            page.show_pdf_page(
                page.rect, self.src, pno=question.page_number, clip=question.bound
            )

        return output
