#创建语音
from gtts import gTTS
import os



def createvoice(text,output):
    tts=gTTS(text=text,lang='zh-CN',slow=False)
    tts.save(output)


if __name__ =="__main__":
    createvoice("白鹤亮翅","./test_files/voices/白鹤亮翅.mp3")
    text="左右搂膝拗步"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="手挥琵琶"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="倒卷肱"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="左揽雀尾"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="右揽雀尾"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="单鞭"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="云手"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="单鞭"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="高探马"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="右蹬脚"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="双峰贯耳"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="转身左蹬脚"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="左下势独立"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="右下势独立"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="左右穿梭"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="海底针"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="闪通臂"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="转身搬拦捶"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="如封似闭"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="十字手"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")
    text="收势"
    createvoice(f"{text}",f"./test_files/voices/{text}.mp3")