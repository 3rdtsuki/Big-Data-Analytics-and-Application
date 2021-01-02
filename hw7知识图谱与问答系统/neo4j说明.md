### neo4j使用教程（基于python）

#### 0.前言

neo4j是一个图数据库，可以基于我们构造的三元组[实体，类型，属性]生成对应的知识图谱。

举个栗子，[Mika,身份,学生]就是一个我们需要的三元组了，等到查询时可能会不知道其中的一或两项。

三元组的知识可以参考：[基于三元组知识图谱的简易问答系统](https://blog.csdn.net/blmoistawinde/article/details/86556844)

本文阐述了如何基于python使用neo4j。

#### 1.安装

参考文章：[安装Neo4j，配置环境变量，python测试](https://blog.csdn.net/xuan314708889/article/details/103858493)

注意几个细节：

- neo4j是基于JAVA开发的，所以首先要安装jdk。

- neo4j console时可能报错Invoke-Neo4j : Could not find java。这时候需要修改环境变量，将JAVA_HOME设置成java.exe的路径（**没有\bin！**）

访问http://localhost:7474/browser，初始用户名、密码均为neo4j。

#### 2.安装py2neo

py2neo是neo4j的python驱动。

命令行中pip install py2neo，这样前期就准备完毕了。

#### 3.代码实现

neo4j采用类似SQL的SPARQL语句来对图数据库操作

一个非常好的例子https://gitee.com/fangchaa/WEB_KG，但有些需要改动

首先将三元组以Mika\$$身份\$$学生的格式存在./triples.txt中

```python
from neo4j import GraphDatabase

# 添加节点和关系的SPARQL语句
def add_node(tx, name1, relation, name2):
    tx.run("MERGE (a:Node {name: $name1}) "
           "MERGE (b:Node {name: $name2}) "
           "MERGE (a)-[:" + relation + "]-> (b)",
           name1=name1, name2=name2)
    
# 启动
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
with driver.session() as session:
    # 读取三元组文件
    lines = open('./triples.txt', 'r',encoding="utf-8").readlines()
    for i, line in enumerate(lines):
        arrays = line.split('$$')
        name1 = arrays[0]
        relation = arrays[1].replace('：', '').\
        replace(':', '').replace('　', '').replace(' ', '').\
        replace('【', '').replace('】', '')
        name2 = arrays[2]
        print(str(i))
        try:
            # 调用add_node函数添加节点和关系
            session.write_transaction(add_node, name1, relation, name2)
            except Exception as e:
                print(name1, relation, name2, str(e))
```

然后进入到http://localhost:7474/browser，选择左边的DataBase，点击Node Labels的Node，这样就可以看到这张图更新啦。

