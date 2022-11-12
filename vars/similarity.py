import spacy
from apps.firebase import db

nlp = spacy.load('en_core_web_md')


def process_text(text):
    doc = nlp(text.lower())
    result = []
    for token in doc:
        if token.text in nlp.Defaults.stop_words:
            continue
        if token.is_punct:
            continue
        result.append(token.lemma_)
    return " ".join(result)


def get_all_documents(team_id):
    document_col = db.collection('teams').document(team_id).collection('documents')
    doc_array = [doc.to_dict() for doc in document_col.get()]
    return doc_array


def find_similarity(doc_id, team_id):
    all_docs = [(temp['id'], temp['content']) for temp in get_all_documents(team_id)]
    document = db.collection('teams').document(team_id).collection('documents').document(doc_id).get().to_dict()
    doc = (document['id'], document['content'])
    doc1 = nlp(process_text(doc[1]))
    results = []

    for doc2 in all_docs:
        sim = doc1.similarity(nlp(process_text(doc2[1])))
        results.append((doc2[0], sim))

    results.sort(key=lambda x:x[1],reverse=True)
    return(results)