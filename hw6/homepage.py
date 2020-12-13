import os
import spaceVector
sv = spaceVector.SpaceVectorModel()
sv.username=input("请输入用户名：")
user_college={'1813055':'cc'}
while True:
    num=input("1.站内查询\n2.全站查询\n3.查询日志\n4.清空日志\n5.退出系统\n请选择服务内容（输入x退出）：")
    if num=='1':
        sv.part_search()
    elif num=='2':
        sv.all_search()
    elif num=='3':
        print("查询日志：")
        with open(r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+sv.username+"_log.txt","r",
                  encoding="utf-8")as f:
            lines=f.readlines()
            for line in lines:
                print(line)
        continue
    elif num=='4':
        with open(r"C:\Users\Mika\Desktop\信息检索\1813055_赵书楠_hw6"+os.sep+sv.username+"_log.txt","w",
                  encoding="utf-8")as f:
            f.write(' ')
        print("日志已清空！")
    else:
        print("欢迎下次使用~")
        break
    print("\n")