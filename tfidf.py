import math
doc=["new home sales top forecasts","home sales rise in july",
      "increase in home sales in july","july new home sales rise"]
def tf(term,i):# term在doc[i]的词频（就是出现次数）
    word_list=doc[i].split(' ')
    cnt=0
    for word in word_list:
        if word==term:
            cnt+=1
    return cnt

def idf(term):
    cnt=0
    for i in range(len(doc)):
        word_list=doc[i].split(' ')
        if term in word_list:
            cnt+=1
    return math.log(len(doc)/cnt,2)

if __name__=="__main__":
    dic=[]
    for i in range(len(doc)):
        word_list = doc[i].split(' ')
        for word in word_list:
            if word not in dic:
                dic.append(word)
    dic=sorted(dic)
    for t in dic:
        print(t,idf(t))
    
    for d in range(len(doc)):
        for t in dic:
            if tf(t,d)>0:
                print(1+math.log(tf(t,d)),end=" ")
            else:
                print(0, end=" ")
        print()
