import json

from DataProcess.Document import Document
class HotpotQA:
    name = "HotpotQA"
    def __init__(self,data):
        self.data = data
        self.id = data['_id']
        self.type = data['type']
        self.level = data['level']
        self.question = data['question']
        self.answer = data['answer']
        self.context = data['context']
        self.documents = self.dealContext()
        self.supporting_facts = data['supporting_facts']
        # self.facts = self.dealFacts()
 
    def dealContext(self):
        documents = []
        for paper in self.context:
            doc = Document(title=paper[0],context=paper[1])
            documents.append(doc)
        return documents

    def dealFacts(self):

        titles = [doc.title for doc in self.documents]
        facts = []
        for fact in self.supporting_facts:
            fact_title = fact[0]
            fact_index = fact[1]
            title_index = titles.index(fact_title)
            fact_context = self.documents[title_index].context[fact_index]
            facts.append([fact_title, fact_context])
        return facts

    def __str__(self):
      # 构建文档式子
        knowledges = ""
        documents = self.documents
        for doc in documents:
          knowledge = f"{doc.title}\n" + '\n-'.join(doc.context)
          knowledges += knowledge
        return knowledges
    
    def get_knowledge(self,args):
        if not args.retrieval:
            return self.__str__()
        else:
            return  self.__str__()







