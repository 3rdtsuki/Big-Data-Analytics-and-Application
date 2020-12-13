"""
直接计算cos<q,d>，以查询词为词语集合，只去研究这部分词语
"""
import math
import os
import re
import jieba
import csv


# 实现argsort, 返回排序后的索引
def my_argsort(array):
    return sorted(range(len(array)), key=lambda i: array[i], reverse=True)

# 将path转为url，因为正反斜杠的replace有蜜汁bug，所以都先替换成$，再split
def path2url(path):
    path = path.replace("/", "$").replace("\\", "$")
    path_pieces = path.split("$")
    url = ""
    for piece in path_pieces[3:]:
        url += '/' + piece
    if url[-4:] == "html":
        url = url[:-1]
    url = "https:/" + url

    n = len(url)
    url = url[:n - 5]  # 去掉.txt
    return url

# 空间向量模型
class SpaceVectorModel:
    def __init__(self):
        self.cnt = 0
        self.query = []
        self.file_paths = []
        self.url_title = {}
        self.college=""
        self.N=0
        self.college_list = ["cc", "cs", "history"]
        # 各学院网页个数
        self.node_num_dict = {"cc": 1523, "cs": 857, "history": 824}
        self.username=""

    # 除去html中所有标签，分词，并保存到当前目录下
    def cut_and_save(self, file_path):
        self.cnt += 1
        print(self.cnt, file_path)
        with open(file_path, "r", encoding="utf-8")as f:
            html = f.read()
        # 除掉标点、字母和数字
        text = re.sub('[a-zA-Z0-9(){}".$;=<>#/!,.\-&\':_|\[\]\+！：“”？?【】——、，。]', '', html)
        pattern = re.compile(r'<[^>]+>', re.S)
        text = pattern.sub('', text).replace(" ", "").replace("\n", "").replace("\t", "")

        # 分词
        seg = jieba.cut(text, cut_all=False)
        cut_result = ' '.join(seg)

        # 写入文档
        with open(file_path + ".txt", "w", encoding="utf=8")as f:
            f.write(cut_result)
        return text

    # 获得所有html的路径，然后文本处理，写入txt文件
    def get_file_path(self, path):
        for fpathe, dirs, fs in os.walk(path):
            for f in fs:
                filepath = os.path.join(fpathe, f)  # html路径
                # # 分词，第一次要把这里的注释去掉
                # if filepath[-5:]==".html":
                #     self.cut_and_save(filepath)
                if filepath[-9:] == ".html.txt":
                    self.file_paths.append(filepath)

    # 向量空间模型，生成词向量（以文档和查询词的并集去重为词袋），计算相似度
    def sim(self, query, file):
        with open(file, "r", encoding="utf-8")as f:
            text = f.read()
        text = text.split(" ")

        word_list = []  # 去重，得到词袋
        for word in text + query:
            if word not in word_list:
                word_list.append(word)
        file_dict = {}
        query_dict = {}
        for word in word_list:
            file_dict[word] = 0
            query_dict[word] = 0
        for word in text:
            file_dict[word] = 1
        for word in query:
            query_dict[word] = 1
        file_vec = list(file_dict.values())
        query_vec = list(query_dict.values())

        son = mum_l = mum_r = 0
        for i in range(len(file_vec)):
            mum_l += file_vec[i] ** 2
            mum_r += query_vec[i] ** 2
            son += file_vec[i] * query_vec[i]
        result = son / (math.sqrt(mum_l) * math.sqrt(mum_r))
        return result

    def entrance(self):
        # 获取网页标题
        csv.field_size_limit(500 * 1024 * 1024)
        with open(r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6" + os.sep + self.college + os.sep + "pageindex.csv", "r",
                  encoding="utf-8")as f:
            reader = csv.reader(f)
            for index, url, title in reader:
                self.url_title[url] = title
        # 计算每个文件和查询词的相似度
        sim_list = []
        # 标题含有查询词，加上权重
        for file in self.file_paths:
            s = self.sim(self.query, file)
            # 如果查询词在标题中出现，需要前移
            title_words = jieba.cut(self.url_title[path2url(file)], cut_all=False)
            title_words = "/".join(title_words).split("/")
            for t_word in title_words:
                for q_word in self.query:
                    if t_word == q_word:
                        s += 0.2
                        break
            sim_list.append(s)
            # 注意加入数组之后，sim要记得减回去，保证下一次查询的正确性

        sorted_index = my_argsort(sim_list)

        # 相似度最高的
        result_list = []
        for i in range(20):
            index = sorted_index[i]
            result_list.append(
                [i + 1, path2url(self.file_paths[index]), self.url_title[path2url(self.file_paths[index])], sim_list[index]])
        return result_list

    # 将每个学院的搜索结果合并为最终结果
    def merge_result(self, result_list):
        sim_list = []
        for line in result_list:
            sim_list.append(line[3])
        sorted_index = my_argsort(sim_list)

        result_list_merged=[]
        for i in range(20):
            index = sorted_index[i]
            result_list_merged+=result_list[index]
            return result_list_merged
    """
    第一种搜索：给定学院名称，只在这个范围内搜索
    """
    def part_search(self):
        while True:
            college = input("请输入学院简称：")
            self.college=college
            if self.college not in self.college_list:
                print("学院不存在，请重新输入")
            else:
                break
        while True:
            # 一定注意每次初始化
            self.__init__()
            self.college = college
            self.N = self.node_num_dict[self.college]
            # 获得目录下所有文件路径
            self.get_file_path(
                r"D:\ir_hw6_search_engine" + os.sep + self.college + os.sep + self.college + ".nankai.edu.cn")

            query = input("请输入查询词（输入x退出）：")
            if query=="x":
                break
            self.save_log(query)
            seg = jieba.cut(query, cut_all=False)
            query = '/'.join(seg).split("/")
            for q in query:
                if q != ' ':
                    self.query.append(q)

            result_list = self.entrance()
            print("查询结果：")
            for line in result_list:
                for i in range(len(line) - 1):
                    print(line[i], end=" ")
                print()

    """
    第二种搜索：全局搜索
    把每个学院都搜一遍
    """
    def all_search(self):
        while True:
            self.__init__()
            query = input("请输入查询词（输入x退出）：")
            if query=="x":
                break
            self.save_log(query)
            seg = jieba.cut(query, cut_all=False)
            query = '/'.join(seg).split("/")
            for q in query:
                if q!=' ':
                    self.query.append(q)

            result_list = []
            for college in self.college_list:
                self.college=college
                self.N = self.node_num_dict[self.college]
                self.get_file_path(
                    r"D:\ir_hw6_search_engine" + os.sep + self.college + os.sep + self.college + ".nankai.edu.cn")
                result_list.append(self.entrance())

            result_list_merged = self.merge_result(result_list)
            print("查询结果：")
            for line in result_list_merged:
                for i in range(len(line)-1):
                    print(line[i], end=" ")
                print()

    # 保存查询日志
    def save_log(self,line):
        with open(r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+self.username+"_log.txt","a",
                  encoding="utf-8")as f:
            f.write(line+' ')