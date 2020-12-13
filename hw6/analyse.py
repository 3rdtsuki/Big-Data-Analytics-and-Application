"""
temp.py:分析爬取的html页面
"""
import os
import re
import csv


# 分析爬取的html页面
class AnalyseHTML:
    def __init__(self):
        self.file_paths = []  # 所有html文档路径
        self.url_describe = []  # 全部元组<url,锚文本>：[[1,"眠眠"],[2,"mianmian"]]
        self.url_title = {}  # 标题
        self.url_index = {}  # 字典<url,no>：{path1:1}
        self.url2url = []  # 字典<url_index,指向的url>：[[1,2],[1,3]]，方便pagerank
        self.index = 0  # 所有链接数
        self.college = ""  # 当前学院名称

    def url2index(self, url):
        return self.url_index[url]

    # 将一个二维数组写入csv尾部
    def write_into_csv(self, path, items):
        with open(path, 'w', encoding="utf-8", newline="")as fp:
            writer = csv.writer(fp)
            writer.writerows(items)

    # 获得所有html文档的路径
    def get_file_path(self, path):
        for fpathe, dirs, fs in os.walk(path):
            for f in fs:
                filepath = os.path.join(fpathe, f)  # html路径
                # 删除index.html，无效网页
                if filepath[-10:] == "index.html":
                    os.unlink(filepath)
                    continue
                if filepath[-5:] == ".html":
                    self.file_paths.append(filepath)

    """
    一般来说分析得到的url是这种格式："../../../13291/list.html"
    但也有"13291/list.html"
    真正的url是https://cc.nankai.edu.cn/13291/list.htm
    path=r"D:/ir_hw6_search_engine/cc/cc.nankai.edu.cn/13291/list.html"
    注意html改成htm
    """

    # 提取文档中所有url，并建立索引，写入
    def extract_url(self, path):
        # 将path转为url
        path_pieces = path.split("\\")
        url = ""
        for piece in path_pieces[3:]:
            url += '/' + piece
        if url[-4:] == "html":
            url = url[:-1]
        college_head = "https://"+self.college+".nankai.edu.cn/"
        url = "https:/" + url
        # 打开html
        try:
            with open(path, "r", encoding="utf-8") as sf:
                html = sf.read()
        except:  # 如果无法用 utf8编码，删除文件
            os.unlink(path)
            return

        # 得到标题
        title = re.findall('<title>(.*?)</title>', html)
        if len(title) == 0:
            os.unlink(path)
            return
        self.url_title[url] = title[0]
        # 赋予序号
        if url not in self.url_index.keys():
            self.index += 1
            self.url_index[url] = self.index
        print(self.url_index[url], url, title[0])

        # 得到utl，锚文本对
        tuples = re.findall('<a.*?href="(.+.html)".*?>(.*?)</a>', html)
        for item in tuples:
            linked_url = item[0]
            while linked_url[:3] == "../":  # 去掉头部../
                linked_url = linked_url[3:]
            linked_url = college_head + linked_url

            if linked_url[-4:] == "html":
                linked_url = linked_url[:-1]

            if linked_url not in self.url_index.keys():  # url没出现过
                self.index += 1  # 出现过的url数++
                self.url_index[linked_url] = self.index  # 编号映射
                self.url_describe.append([self.url_index[linked_url], item[1]])  # 锚文本

            self.url2url.append([url, linked_url])  # 存储s->t

    # 写索引文件、锚文本文件和链接文件
    def write_files(self, dir_path):
        index_list = []
        for key in self.url_index.keys():
            try:
                index_list.append([self.url_index[key], key, self.url_title[key]])
            except:
                index_list.append([self.url_index[key], key, "empty"])
        # 写入序号，url，标题
        print("begin writing pageindex...")
        self.write_into_csv(dir_path + r"\pageindex.csv",
                            index_list)

        # url_id-锚文本文件
        print("begin writing description...")
        self.write_into_csv(dir_path + r"\description.csv",
                            self.url_describe)
        url2url = []
        for start, end in self.url2url:

            if [self.url_index[start], self.url_index[end]] not in url2url:
                url2url.append([self.url_index[start], self.url_index[end]])

        # pagerank输入文件
        print("begin writing pagelink...")
        self.write_into_csv(dir_path + r"\pagelink.csv", url2url)

    def entrance(self):
        for filepath in self.file_paths:
            self.extract_url(filepath)
        dir_path = r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+self.college
        """写文件！！！"""
        print("begin writing files...")
        self.write_files(dir_path)


if __name__ == "__main__":
    # 分析url模块
    ana = AnalyseHTML()
    ana.college="history"
    # path=r"D:/ir_hw6_search_engine/cc/cc.nankai.edu.cn"
    ana.get_file_path(r"D:\ir_hw6_search_engine"+os.sep+ana.college+os.sep+ana.college+".nankai.edu.cn")  # 得到目录下所有html路径
    ana.entrance()  # 分析入口
    print(ana.index)

