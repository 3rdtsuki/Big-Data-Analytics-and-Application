import csv
import os

# 将一个二维数组写入csv尾部
def write_into_csv(path, items):
    with open(path, 'w', encoding="utf-8", newline="")as fp:
        writer = csv.writer(fp)
        writer.writerows(items)

# 实现argsort, 返回排序后的索引
def my_argsort(array):
    return sorted(range(len(array)), key=lambda i: array[i], reverse=True)


def ResolveGraphFile(graph_path):
    with open(graph_path) as graph_file:
        s = graph_file.readlines()
    adj_table = {}
    reverse_table = {}
    no_line = 0
    number_of_vertices = 0
    flag = [0] * 2000
    maxm = 0
    for line in s:
        no_line += 1
        temp = line.strip().split(',')
        temp[0] = int(temp[0])
        temp[1] = int(temp[1])
        if temp[0] not in adj_table:
            adj_table.update({temp[0]: {temp[1]}})
        elif temp[1] not in adj_table[temp[0]]:
            adj_table[temp[0]].update({temp[1]})

        flag[temp[0]] = flag[temp[1]] = 1  # start and end have appeared
        maxm = max(maxm, temp[0], temp[1])
        if temp[1] not in reverse_table:
            reverse_table.update({temp[1]: {temp[0]}})
        elif temp[0] not in reverse_table[temp[1]]:
            reverse_table[temp[1]].update({temp[0]})
    for i in flag:
        number_of_vertices += i
    print("number of vertices: ", number_of_vertices)
    print("number of edges: ", no_line)
    print("number of started vertices: ", len(adj_table))
    print("max number: ", maxm)

    return adj_table, maxm, reverse_table


def initialize_m(adj_table):
    m = [0] * (n + 1)
    for i in adj_table.keys():
        m[int(i)] = 1 / len(adj_table[i])
    return m


def getDelta(n, r, m, beta, reverse_table):
    # r_new = [0] * (n+1) ## 更改为:
    r_new = [(1 - beta) / n] * (n + 1)  # 修spider trap
    sum_r = 0
    for i in range(1, n + 1):
        if i in reverse_table.keys():
            for j in reverse_table[i]:
                # r_new[i] += m[j]*r[j] # r_new[i] *= beta ## 更改为:
                r_new[i] += m[j] * r[j] * beta
        sum_r += r_new[i]
    for i in range(1, n + 1):
        r_new[i] += (1 - sum_r) / n  # 修黑洞
    delta = 0
    for i in range(1, 1 + n):
        delta += abs(r_new[i] - r[i])
    return delta, r_new


if __name__ == '__main__':
    index_url={}
    csv.field_size_limit(500 * 1024 * 1024)

    college="cc"# 学院名
    with open(r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+college+os.sep+"pageindex.csv","r",encoding="utf-8")as f:
        reader = csv.reader(f)
        for index,url,title in reader:
            index_url[int(index)]=[url,title]

    # 排序和输出结果
    path = r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+college+os.sep+"pagelink.csv"
    adj_table, n, reverse_table = ResolveGraphFile(path)
    beta = 0.85
    r = [1 / n] * (n + 1)
    m = initialize_m(adj_table)
    delta = 1
    loop_times = 0  # 记录迭代次数
    while (delta > 0.00000001):  # 迭代更新
        delta, r = getDelta(n, r, m, beta, reverse_table)
        loop_times += 1
    print('loop times: %d\nresult:' % loop_times)
    sorted_index=my_argsort(r)

    result=[]
    path=r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+college+os.sep+"pagerank_result.csv"
    for i in range(100):
        index = sorted_index[i]
        print(i + 1,index, r[index],index_url[index][0],index_url[index][1])
        result.append([i + 1,index, r[index],index_url[index][0],index_url[index][1]])
    #write_into_csv(path,result)



