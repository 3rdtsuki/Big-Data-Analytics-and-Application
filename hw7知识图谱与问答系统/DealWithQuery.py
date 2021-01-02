import os
import re
import jieba
import csv
from jieba import posseg
from neo4j import GraphDatabase

attrs = ['性别', '部门', '职务', '职称', '学历', '专业', '电话', '邮箱', '研究方向']
# 提取标签
class ExtractLabel:
    def __init__(self):
        self.label_table = []
        self.file_paths = []

    # 将一个高维数组写入csv尾部
    def write_into_csv(self, path, items):
        with open(path, 'w', encoding="utf-8", newline="")as fp:
            writer = csv.writer(fp)
            writer.writerows(items)

    # 分析html页面，获得个人信息
    def get_label(self, file):
        with open(file, "r", encoding="utf-8")as f:
            html = f.read()
        tuples = re.findall(r'<span>(.*?)</span>', html)
        if len(tuples) == 0:
            return
        filter_words = ["发布时间：", "第一页"]  # 过滤词
        if tuples[0] in filter_words:
            return
        self.label_table.append(tuples)

    # 获得所有html的路径
    def get_file_path(self, path):
        for fpathe, dirs, fs in os.walk(path):
            for f in fs:
                filepath = os.path.join(fpathe, f)  # html路径
                # 分词，第一次要把这里的注释去掉
                if filepath[-5:] == ".html":
                    self.file_paths.append(filepath)

    def print_list(self, l):
        for i in l:
            print(i)

    def entrance(self, path):
        self.get_file_path(path)
        for file in self.file_paths:
            self.get_label(file)
        # self.write_into_csv("./information.csv",self.label_table)


class QuerySection:
    def __init__(self):
        self.query=""
        self.label_dict={}
        self.word_flag=[]

    # 读取信息表
    def read_csv(self):
        path = "./information.csv"
        csv.field_size_limit(500 * 1024 * 1024)
        with open(path, "r", encoding="utf-8")as csvfile:
            reader = csv.reader(csvfile)
            for line in reader:
                self.label_dict[line[0]] = line[1:]

    # 查询分词，获得词性
    def get_word_flag(self, raw_question):
        raw_question = raw_question.strip()
        # userdict里面存储不可拆分的词及其词性
        jieba.load_userdict("./userdict.txt")
        clean_question = re.sub("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）]+", "",
                                raw_question)
        # 判断词性
        question_seged = jieba.posseg.cut(str(clean_question))
        question_word, question_flag = [], []
        for w in question_seged:
            temp_word = [w.word,w.flag]
            self.word_flag.append(temp_word)
            # 预处理问题
            word, flag = w.word, w.flag
            question_word.append(str(word).strip())
            question_flag.append(str(flag).strip())
        assert len(question_flag) == len(question_word)
        #print(self.word_flag)

    def search(self):
        # nr代表人
        attr=entity=""
        for word,flag in self.word_flag:
            if flag=='nr':
                entity=word
            elif flag=='n':
                attr=word
        # 找到attr在attrs的位置
        for i in range(len(attrs)):
            if attrs[i]==attr:
                print(self.label_dict[entity][i])
                break

    def entrance(self,query):
        self.query=query
        self.read_csv()
        self.get_word_flag(self.query)
        self.search()


# 构建知识图谱
class KnowledgeGraph:
    def __init__(self):
        self.label_dict = {}

    def print_dict(self, l):
        for i in l:
            print(i, l[i])

    # 读取信息表
    def read_csv(self):
        path = "./information.csv"
        csv.field_size_limit(500 * 1024 * 1024)
        with open(path, "r", encoding="utf-8")as csvfile:
            reader = csv.reader(csvfile)
            for line in reader:
                self.label_dict[line[0]] = line[1:]
        self.print_dict(self.label_dict)

    # 生成三元组并写入文件
    def gen_triples(self):
        triple_path = './triples.txt'
        with open(triple_path, 'w', encoding="utf-8")as f:
            for key in self.label_dict.keys():
                for i in range(len(attrs)):
                    # 可能为空
                    if self.label_dict[key][i] == '' or self.label_dict[key][i] == '无':
                        continue
                    f.write(key + '$$' + attrs[i] + '$$' + self.label_dict[key][i] + "\n")
    
    # 添加节点和关系
    def add_node(self, tx, name1, relation, name2):
        tx.run("MERGE (a:Node {name: $name1}) "
               "MERGE (b:Node {name: $name2}) "
               "MERGE (a)-[:" + relation + "]-> (b)",
               name1=name1, name2=name2)

    def make_graph(self):
        # cmd输入neo4j console启动neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            lines = open('./triples.txt', 'r', encoding="utf-8").readlines()
            for i, line in enumerate(lines):
                arrays = line.split('$$')
                name1 = arrays[0]
                relation = arrays[1].replace('：', ''). \
                    replace(':', '').replace('　', '').replace(' ', ''). \
                    replace('【', '').replace('】', '')
                name2 = arrays[2]
                print(str(i))
                try:
                    session.write_transaction(self.add_node, name1, relation, name2)
                except Exception as e:
                    print(name1, relation, name2, str(e))

    def entrance(self):
        self.read_csv()
        self.gen_triples()
        self.make_graph()


if __name__ == "__main__":
    # el=ExtractLabel()
    # el.entrance(r"D:\ir_hw6_search_engine\cc\cc.nankai.edu.cn")

    kg = KnowledgeGraph()
    kg.entrance()

    qs=QuerySection()
    while True:
        query = input("请输入问题（输入x退出）：")
        if query=='x':
            break
        qs.entrance(query)

