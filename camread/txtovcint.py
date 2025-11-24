import pyttsx3

def txtovcint(text,engine=pyttsx3.init()):
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    
    # 可选：选择语音（Windows下可能有多个语音包）
    voices = engine.getProperty('voices')
    # 例如：选择第一个女声（索引可能因系统而异）
    # engine.setProperty('voice', voices[1].id)
    engine.say(text)

    # 等待语音播放完成
    engine.runAndWait()

    