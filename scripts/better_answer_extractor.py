import fitz #PyMuPdf


def before_17(doc: fitz.Document):
    words = doc[1].get_text_words(clip=fitz.Rect(155, 105, 450, 700))

    answers = []

    for i in range(len(words)):
        try:
            qn = int(words[i][4])
            answers.append((qn, words[i + 1][4]))
        except:
            pass
    return answers


def after_17(doc: fitz.Document):

    words = doc[1].get_text_words(clip=fitz.Rect(70, 85, 140, 770))
    words.extend(doc[2].get_text_words(clip=fitz.Rect(70, 85, 140, 770)))

    answers = []

    for i in range(len(words)):
        try:
            qn = int(words[i][4])
            answers.append((qn, words[i + 1][4]))
        except:
            pass
    return answers
