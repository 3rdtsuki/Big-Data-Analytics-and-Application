### 信息检索第六次作业——南开百事通

本次作业要求针对南开校内网站构建Web搜索引擎。

#### 0.操作演示

因为某些原因，演示视频没法录声音了orz，所以我在这里首先向您以文字的方式介绍一下功能。

（0）首先，运行homepage.py，提示“请输入用户名”，可以输入任意用户名。

回车之后，出现如下选项，可以选择需要的功能。

<img src="C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213222313929.png" alt="image-20201213222313929" style="zoom:67%;" />

（1）输入1，将提示输入学院简称（计算机学院为cc），和查询词，回车得到结果：

![image-20201213222444237](C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213222444237.png)

也支持短语查询：如“人工 智能”：

![image-20201213223051629](C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213223051629.png)

（2）输入2，进行全站查询：以查询软件学院的王超老师为例

![image-20201213225851345](C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213225851345.png)

（3）输入3，可以查看查询日志：

![image-20201213223159354](C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213223159354.png)

（4）输入4，清空日志

<img src="C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213223231363.png" alt="image-20201213223231363" style="zoom:67%;" />

（5）退出：查询中输入x即可退出，主目录下输入5退出。

<img src="C:\Users\Mika\AppData\Roaming\Typora\typora-user-images\image-20201213230458228.png" alt="image-20201213230458228" style="zoom:67%;" />

#### 1.网页抓取(HTTrack Website Copier)

因为可以自由选取工具，所以我使用了网页抓取软件HTTrack Website Copier抓取网页。输入要爬取的主站、爬取文件类型、爬取最大深度等关键规则信息，该软件可以自动进行爬取，并将页面按照url路径在相应文件夹中存为html格式。

#### 2.文本索引(analyse.py)

爬取大量页面后，为了进行后续操作，必须对这些url进行索引构建。这里我就在根据页面内容获取锚文本的同时进行索引构建。

维护一个变量index，遍历每一个页面内容，只要遇到没出现过的链接就让index++。通过字典建立url到索引的映射，同时获得页面的标题，将这些信息保存至每个学院目录下的pageindex.csv文件中。例如：

| index | url                               | title          |
| ----- | --------------------------------- | -------------- |
| 1     | https://cc.nankai.edu.cn/main.htm | 计算机学院主页 |

同时为了完成下面的链接分析，将链接对以<start,end>的方式保存至文件pagelink.csv中。

将网页的锚文本（如果没有则为empty），<index，锚文本>的方式保存至description。

#### 3.链接分析(pagerank.py)

使用PageRank算法进行链接分析，评估网页权重，给出排名。

PageRank的具体实现方法是：

> 输入：起点，终点
>
> 生成邻接表
>
> 初始每个节点能量ri为1/n，mi=1/di，di是出度的倒数
>
> while(delta>epsilon):
> 	if j->i:
> 		r'i+=mj*rj
>         delta=sum(|r'i-ri|)
>
> 输出：最终的r列表

将结果保存至pagerank_result.csv文件中。

因为上学期选了杨征路老师的大数据计算及应用，所以还附带了“黑洞”和spider trap两种异常情况的处理方法，使结果更加可靠，详见pagerank.py文件。

#### 4.查询(spaceVector.py)

本次作业采用向量空间模型VSM对查询语句和文档进行相似度计算。

首先是预处理工作，遍历所有html页面，然后去除文本内所有的中英文标点符号和数字，采用jieba模块进行分词，将内容保存到同目录下同名的txt文件中，之后查询时只需要遍历这些txt就可以了。

我计算相似度的方法十分直观，就是现将查询语句进行分词，和一篇文档内去重后的所有词语合起来构成一个词袋，并分别根据出现词语与否构建词向量。

如：file=["a","b","c"],query=["c","d"]

则file_vec=[1,1,1,0],query_vec=[0,0,1,1]

就这样简单地对查询语句和所有文档计算夹角余弦作为相似度，得到排序后的列表。（代码详见spaceVector.py的sim函数）

当然这还不够，如果某个网页标题带有查询词，应该优先显示，所以我将标题中出现过查询词的网页的相似度加上了一个权重（如0.2），然后再输出排名。注意加入数组之后，s要记得减回去，保证下一次查询的正确性。

##### 站内查询

即对所有校内网站进行搜索，返回相似度最高的前20个网站。实际上是由个性化查询的结果组合排序而来。（一定要注意每次查询前都要初始化，不然结果可能会受上次查询影响！）

代码见spaceVector.py的all_search函数。

##### 短语查询

支持短语查询，一方面可以利用jieba分词，另一方面可以手工加空格分隔词语。

##### 查询日志

支持输出历史搜索记录，同时支持清除历史记录。很简单的方法就是根据用户名的不同在本地创建一个只属于该用户的文档，只要查询就将查询语句写在最后即可，删除相当于写入一个空白字符。

#### 5.个性化查询(homepage.py)

这一项我做的个性化查询就是根据输入的学院来在某个学院的网站下进行查询。其实这一步是站内查询的基础，因为我爬取的页面是按照url的方式创建目录存储的，所以只需要在该学院的目录下遍历内容即可。

代码见spaceVector.py的part_search函数。

#### 6.写在最后

因为本人本学期课程和作业量巨大，所以只完成了这些功能，也没有做界面，很是遗憾，希望助教老师多多包涵，谢谢！
