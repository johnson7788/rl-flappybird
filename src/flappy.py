from itertools import cycle
import random
import sys
import os
import argparse
import pickle
import datetime
import wandb

import pygame
from pygame.locals import *

sys.path.append(os.getcwd())

from enum import Enum
#以下模式中，我们根据arguments只会选择一个
class Mode(Enum):
    NORMAL = 1   #初始模式
    PLAYER_AI = 2  #用AI玩游戏
    TRAIN = 3   # 有UI的方式训练
    TRAIN_NOUI = 4   #训练模式中，没有UI的方式训练
    TRAIN_REPLAY = 5  #REPLAY的模式训练

from bot import Bot

# 初始化bot
bot = Bot()
# 屏幕尺寸
SCREENWIDTH = 288
SCREENHEIGHT = 512
# 管道上部和下部之间的间隙
PIPEGAPSIZE = 100
# base是地面, 计算地面的高度
BASEY = SCREENHEIGHT * 0.79
# 图像，声音和hitmask  dicts
IMAGES, SOUNDS, HITMASKS = {}, {}, {}
# 设置init模式, MODE这里为1
MODE = Mode.NORMAL

# 所有可能的玩家列表（3个flap的3个位置）, 3个鸟，不同颜色，每个鸟分为3种姿势，翅膀在上面，中间，下面

PLAYERS_LIST = (
    # red bird
    (
        "data/assets/sprites/redbird-upflap.png",
        "data/assets/sprites/redbird-midflap.png",
        "data/assets/sprites/redbird-downflap.png",
    ),
    # blue bird
    (
        # amount by which base can maximum shift to left
        "data/assets/sprites/bluebird-upflap.png",
        "data/assets/sprites/bluebird-midflap.png",
        "data/assets/sprites/bluebird-downflap.png",
    ),
    # yellow bird
    (
        "data/assets/sprites/yellowbird-upflap.png",
        "data/assets/sprites/yellowbird-midflap.png",
        "data/assets/sprites/yellowbird-downflap.png",
    ),
)

# 所有的背景
BACKGROUNDS_LIST = (
    "data/assets/sprites/background-day.png",
    "data/assets/sprites/background-night.png",
)

# 有红色和绿色的管道
PIPES_LIST = ("data/assets/sprites/pipe-green.png", "data/assets/sprites/pipe-red.png")

# image, Width, Height
WIDTH = 0
HEIGHT = 1
#各种尺寸
IMAGES_INFO = {}
IMAGES_INFO["player"] = ([34, 24], [34, 24], [34, 24])  #3种颜色的小鸟的尺寸
IMAGES_INFO["pipe"] = [52, 320]   #管道的尺寸
IMAGES_INFO["base"] = [336, 112]
IMAGES_INFO["background"] = [288, 512]

SCORES = []
EPISODE = 0
MAX_SCORE = 10_000_000
RESUME_ONCRASH = False

def getNextUpdateTime():
    return datetime.datetime.now() + datetime.timedelta(minutes = 5)
# 时间 2021-03-24 11:04:37.321958
NEXT_UPDATE_TIME = getNextUpdateTime()

def main():
    global HITMASKS, SCREEN, FPSCLOCK, FPS, bot, MODE, SCORES, EPISODE, MAX_SCORE, RESUME_ONCRASH

    parser = argparse.ArgumentParser("flappy.py")
    parser.add_argument("--fps", type=int, default=60, help="每秒帧数，正常模式下默认值：25，Replay模式是20帧，AI玩游戏模式：60 ")
    parser.add_argument("--episode", type=int, default=10000, help="episode 数量，默认值：10000 ")
    parser.add_argument("--ai", action="store_true", help="是否用AI agent玩游戏 ")
    parser.add_argument("--train", action="store", default='normal', choices=('normal', 'noui', 'replay'), help="训练AI agent玩游戏，从“replay”模式下的最后50步replay游戏 ")
    parser.add_argument("--resume", action="store_true", help="在崩溃前从最后50步恢复游戏, 对于罕见的情况下修正飞行轨迹很有用。但它比普通模式慢了3倍。在replay训练模式下，这个选项会自动启用。")
    parser.add_argument("--max", type=int, default=10_000_000, help="每个episode的最大分数，重启游戏如果agent达到此分数，则默认：10,000,000分")
    parser.add_argument("--dump_hitmasks", action="store_true", help="将HitMasks转储到文件并退出程序，只做这一件事, hitmask,即物体的像素的形状的bool值")
    parser.add_argument("--wandb", action="store_true", help="是否用wandb记录参数")
    args = parser.parse_args()

    FPS = args.fps
    EPISODE = args.episode
    MAX_SCORE = args.max
    RESUME_ONCRASH = args.resume
    if args.wandb:
        wandb.init(project='flappy_bird')
        config = wandb.config
    if args.ai:
        MODE = Mode.PLAYER_AI
    elif args.train == "noui":
        MODE = Mode.TRAIN_NOUI
    elif args.train == "replay":
        MODE = Mode.TRAIN_REPLAY
        RESUME_ONCRASH = True
        FPS = 20
    elif args.train == "normal":
        MODE = Mode.TRAIN
    else:
        MODE = Mode.NORMAL
        FPS = 25

    if args.wandb:
        global usewandb
        usewandb = args.wandb
        config.fps = FPS
        config.episode = EPISODE
        config.max_score = MAX_SCORE
        config.resume_oncrash = RESUME_ONCRASH
        config.mode = MODE

    if MODE == Mode.TRAIN_NOUI:
        # load dumped HITMASKS
        with open("data/hitmasks_data.pkl", "rb") as input:
            HITMASKS = pickle.load(input)
    else:
        # 初始化一个游戏
        pygame.init()
        #  <Clock(fps=0.00)>
        FPSCLOCK = pygame.time.Clock()
        #这是屏幕的宽度和高度
        SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
        #设置游戏的名字
        pygame.display.set_caption("Flappy Bird")

        # 数字精灵，用于显示分数
        IMAGES["numbers"] = (
            pygame.image.load("data/assets/sprites/0.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/1.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/2.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/3.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/4.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/5.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/6.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/7.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/8.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/9.png").convert_alpha(),
        )

        # 游戏结束时的图像
        IMAGES["gameover"] = pygame.image.load("data/assets/sprites/gameover.png").convert_alpha()
        # 游戏开始时的welcome界面
        IMAGES["message"] = pygame.image.load("data/assets/sprites/message.png").convert_alpha()
        # 游戏的地面 base (ground)
        IMAGES["base"] = pygame.image.load("data/assets/sprites/base.png").convert_alpha()

        # 游戏的声音
        if "win" in sys.platform:
            soundExt = ".wav"
        else:
            soundExt = ".ogg"
        #不同的声音
        SOUNDS["die"] = pygame.mixer.Sound("data/assets/audio/die" + soundExt)
        SOUNDS["hit"] = pygame.mixer.Sound("data/assets/audio/hit" + soundExt)
        SOUNDS["point"] = pygame.mixer.Sound("data/assets/audio/point" + soundExt)
        SOUNDS["swoosh"] = pygame.mixer.Sound("data/assets/audio/swoosh" + soundExt)
        SOUNDS["wing"] = pygame.mixer.Sound("data/assets/audio/wing" + soundExt)

    while True:
        if MODE != Mode.TRAIN_NOUI:
            # 如果不是NO UI的训练模式，那么随机选择一个背景
            randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
            # eg: <Surface(288x512x32 SW)>
            IMAGES["background"] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

            #随机选择一种颜色的小鸟, eg: randPlayer: 1
            randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
            #设置选中的小鸟的三种飞行姿势
            IMAGES["player"] = (
                pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
                pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
                pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
            )

            #随机选择一个管道, 管道变成2个，一个是正的，一个是旋转180度后倒立的
            pipeindex = random.randint(0, len(PIPES_LIST) - 1)
            IMAGES["pipe"] = (
                pygame.transform.rotate(pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), 180),
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
            )

            #管道的像素点转换成bool值,知道管道的形状了
            HITMASKS["pipe"] = (getHitmask(IMAGES["pipe"][0]), getHitmask(IMAGES["pipe"][1]))

            #小鸟的像素点转换成bool值，这样就知道小鸟的形状了
            HITMASKS["player"] = (
                getHitmask(IMAGES["player"][0]),
                getHitmask(IMAGES["player"][1]),
                getHitmask(IMAGES["player"][2]),
            )

            if args.dump_hitmasks:
                with open("data/hitmasks_data.pkl", "wb") as output:
                    pickle.dump(HITMASKS, output, pickle.HIGHEST_PROTOCOL)
                sys.exit()
        # 欢迎页面的信息  {'playery': 244, 'basex': 0, 'playerIndexGen': <itertools.cycle object at 0x7ffbb03aaa80>}
        movementInfo = showWelcomeAnimation()
        #开始游戏，返回crash的信息
        crashInfo = mainGame(movementInfo)
        #游戏结束了
        showGameOverScreen(crashInfo)

def showDebugInfo(x, y, vel, pipe):
    white = (255,255,255)
    font = pygame.font.Font(None, 20)
    text = []
    text.append(font.render(str("x, y: {}, {}".format(x, y)), 1, white))
    text.append(font.render(str("V: {}".format(vel)), 1, white))
    text.append(font.render(str("x0, y0: {}, {}".format(int(pipe[0]["x"]-x), int(pipe[0]["y"]-y))), 1, white))
    text.append(font.render(str("x1, y1: {}, {}".format(int(pipe[1]["x"]-x), int(pipe[1]["y"]-y))), 1, white))
    for no, data in enumerate(text):
        SCREEN.blit(data, (0, 20*no))

def showWelcomeAnimation():
    """显示flappy鸟的欢迎屏幕动画"""
    # index of player to blit on screen
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # 迭代器用于每5次迭代后改变playerIndex。
    loopIter = 0
    #计算出小鸟的位置
    playerx = int(SCREENWIDTH * 0.2)
    # IMAGES_INFO包含小鸟，管道，地面和背景的尺寸
    playery = int((SCREENHEIGHT - IMAGES_INFO["player"][0][HEIGHT]) / 2)

    if MODE != Mode.TRAIN_NOUI:
        messagex = int((SCREENWIDTH - IMAGES["message"].get_width()) / 2)
        messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    # 计算出地面左移的数量
    baseShift = IMAGES_INFO["base"][WIDTH] - IMAGES_INFO["background"][WIDTH]

    # player shm 播屏幕上的上下动作
    playerShmVals = {"val": 0, "dir": 1}

    while True:
        """ 取消了按压键functionality"""

        if MODE != Mode.NORMAL:
            if MODE != Mode.TRAIN_NOUI:
                SOUNDS["wing"].play()
            return {
                "playery": playery + playerShmVals["val"],
                "basex": basex,
                "playerIndexGen": playerIndexGen,
            }
        else:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    # make first flap sound and return values for mainGame
                    SOUNDS['wing'].play()
                    return {
                        'playery': playery + playerShmVals['val'],
                        'basex': basex,
                        'playerIndexGen': playerIndexGen,
                    }

        # adjust playery, playerIndex, basex
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)

        # draw sprites
        SCREEN.blit(IMAGES["background"], (0, 0))
        SCREEN.blit(IMAGES["player"][playerIndex], (playerx, playery + playerShmVals["val"]))
        SCREEN.blit(IMAGES["message"], (messagex, messagey))
        SCREEN.blit(IMAGES["base"], (basex, BASEY))

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def updateQtable(score):
    global NEXT_UPDATE_TIME

    if MODE in [Mode.TRAIN, Mode.TRAIN_NOUI, Mode.TRAIN_REPLAY]:
        print("Game " + str(bot.gameCNT) + ": " + str(score))

        justUpdate = False
        if MODE == Mode.TRAIN or score > 100_000 or datetime.datetime.now() > NEXT_UPDATE_TIME:
            bot.dump_qvalues(force=True)
            justUpdate = True
            NEXT_UPDATE_TIME = getNextUpdateTime()

        if score > max(SCORES, default=0) and score > 100_000:
            print("\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("$$$$$$$$ NEW RECORD: %d $$$$$$$$" % score)
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")

        SCORES.append(score)
        
        if bot.gameCNT >= EPISODE:
            if not justUpdate: bot.dump_qvalues(force=True)
            showPerformance()
            pygame.quit()
            sys.exit()


import copy
def mainGame(movementInfo):
    """
    开始游戏
    :param movementInfo: 起始的画面信息
    :return:
    """
    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo["playerIndexGen"]
    #小鸟的位置
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo["playery"]
    # 地面的位置和地面移动的位置， eg: basex: 0,  baseShift:48
    basex = movementInfo["basex"]
    baseShift = IMAGES_INFO["base"][WIDTH] - IMAGES_INFO["background"][WIDTH]

    # 获取2个新管道添加到 upperPipes lowerPipes 列表中。eg: [{'x': 298, 'y': -202}, {'x': 298, 'y': 218}]
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # list of upper pipes， eg:  {dict: 2} {'x': 488, 'y': -202} 和 {dict: 2} {'x': 632.0, 'y': -131}
    upperPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[0]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[0]["y"]},
    ]

    # list of lowerpipe
    lowerPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[1]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[1]["y"]},
    ]
    #管道的默认速度
    pipeVelX = -4

    # 小鸟速度、最大速度、向下加速度、向上拍翼加速度。
    playerVelY = -9  # 沿Y方向的速度，默认与PlayerFlapped相同。
    playerMaxVelY = 10  # 沿Y方向最大速度，最大下降速度
    playerMinVelY = -8  #沿Y的最小速度，最大上升速度
    playerAccY = 1  # 小鸟的下降的加速度
    playerFlapAcc = -9  # 小鸟的飞行速度，即扇动速度
    playerFlapped = False  # 当小鸟扇动翅膀时为真
    #打印分数
    printHighScore = False
    #用于记录最后50个状态，当重新开始的时候
    stateHistory = []
    replayGame = False
    restartGame = False
    steps = 0
    refreshCount = 1
    #开始玩游戏
    while True:
        if MODE != Mode.TRAIN_NOUI:
            #刷新次数更新
            if MODE == Mode.TRAIN_REPLAY and not replayGame and not restartGame:
                refreshCount += 1

            if MODE != Mode.TRAIN_REPLAY or refreshCount % 5000 == 0 or replayGame or restartGame:
                if refreshCount % 5000 == 0:
                    refreshCount = 1
                # event: <Event(4352-AudioDeviceAdded {'which': 0, 'iscapture': 0})>, type=4352
                for event in pygame.event.get():
                    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                    # KEYDOWN: 768, 事件类型等于按键下
                    if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                        if playery > -2 * IMAGES["player"][0].get_height():
                            playerVelY = playerFlapAcc
                            playerFlapped = True
                            SOUNDS["wing"].play()

        if replayGame:
            steps += 1
            if steps >= len(stateHistory):
                return {
                "y": playery,
                "groundCrash": False,
                "basex": basex,
                "upperPipes": upperPipes,
                "lowerPipes": lowerPipes,
                "score": score,
                "playerVelY": playerVelY,
            }
            (playerx, playery, playerVelY, lowerPipes, upperPipes, score, playerIndex) = stateHistory[steps]
        else:
            if MODE in [Mode.TRAIN_NOUI, Mode.TRAIN, Mode.TRAIN_REPLAY] and RESUME_ONCRASH: 
                currentState = [playerx, playery, playerVelY, copy.deepcopy(lowerPipes), copy.deepcopy(upperPipes), score, playerIndex]
                if restartGame and steps < len(stateHistory):
                    stateHistory[steps] = currentState
                else:
                    stateHistory.append(currentState)
                    if len(stateHistory) > 50:
                        stateHistory.pop(0)
            #当不是用户玩游戏的模式时，我们然机器人操作小鸟，playerx: 57, playery: 244, playerVelY: -9，在Y方向的速度, lowerPipes: [{'x': 488, 'y': 216}, {'x': 632.0, 'y': 210}]下方管道
            if usewandb:
                wandb.log({"steps":steps,"playerx":playerx, "playery":playery, "playerVelY":playerVelY })
            # playerx 方向基本不动，因为一直在屏幕中央, y方向上下变化，y方向的速度也在变化
            if MODE != Mode.NORMAL and bot.act(playerx, playery, playerVelY, lowerPipes):
                if playery > -2 * IMAGES_INFO["player"][0][HEIGHT]:
                    playerVelY = playerFlapAcc
                    # 小鸟挥动翅膀
                    playerFlapped = True
                    if MODE != Mode.TRAIN_NOUI and MODE != Mode.TRAIN_REPLAY:
                        SOUNDS["wing"].play()

       # 小鸟采取了行动，现在开始, 判断是否撞击了，eg: [False, False]表示小鸟存活
        crashTest = checkCrash(
            {"x": playerx, "y": playery, "index": playerIndex}, upperPipes, lowerPipes
        )
        if crashTest[0]:
            #print(playerx, playery, playerIndex, upperPipes, lowerPipes)
            if MODE == Mode.TRAIN_REPLAY:
                if not replayGame:
                    restartGame = False
                    replayGame = True
                    steps = -1
                    print("REPLAY GAME for last 50 steps...")
                    continue
                else:
                    replayGame = False

            # Update the q scores
            if MODE in [Mode.TRAIN_NOUI, Mode.TRAIN, Mode.TRAIN_REPLAY]:
                bot.update_scores()

                if len(stateHistory) > 20 and (not restartGame or (restartGame and steps > 10)):
                    updateQtable(score)
                    (playerx, playery, playerVelY, lowerPipes, upperPipes, score, playerIndex) = stateHistory[0]
                    if score > 100_000:
                        print("\n" + "#"*40)
                        print("RESTART FROM LAST 50th state: %s" % bot.get_state(playerx, playery, playerVelY, lowerPipes))
                        print("#"*40 + "\n")
                    score = 0
                    restartGame = True
                    replayGame = False
                    steps = 0      # show the first 100 steps in the new game
                    #print("CONTINUE GAME from death position...")
                    continue

                restartGame = False

            return {
                "y": playery,
                "groundCrash": crashTest[1],
                "basex": basex,
                "upperPipes": upperPipes,
                "lowerPipes": lowerPipes,
                "score": score,
                "playerVelY": playerVelY,
            }

        #判断分数, playerMidPos 小鸟的位置
        playerMidPos = playerx + IMAGES_INFO["player"][0][WIDTH] / 2
        for pipe in upperPipes:
            #当小鸟的位置和管道的位置相距一定距离时，我们给它加一定分数,  小鸟超过一个管道，那么我们给它加1分
            pipeMidPos = pipe["x"] + IMAGES_INFO["pipe"][WIDTH] / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                printHighScore = True
                if MODE not in [Mode.TRAIN_NOUI, Mode.TRAIN_REPLAY]:
                    SOUNDS["point"].play()
                if score >= MAX_SCORE:    #最大得分时终止游戏和重启游戏
                    bot.terminate_game()
                    return {
                        "score": score,
                    }
        #当在训练模式时
        if MODE in [Mode.TRAIN_NOUI, Mode.TRAIN, Mode.TRAIN_REPLAY] and printHighScore and score != 0 and score % 10000==0:
            print("Game " + str(bot.gameCNT+1) + ": reach " + str(score) + "...")
            printHighScore = False

        # playerIndex basex change
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        #小鸟移动
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        #如果小鸟煽动翅膀, 煽动一次翅膀后，我们就不删动翅膀了，只需要煽动一次
        if playerFlapped:
            playerFlapped = False
        #小鸟的初始的高度
        playerHeight = IMAGES_INFO["player"][playerIndex][HEIGHT]
        #小鸟现在的高度
        playery += min(playerVelY, BASEY - playery - playerHeight)

        addPipes = True
        if restartGame:
            steps += 1
            if steps < len(stateHistory):
                (_, _, _, lowerPipes, upperPipes, _, _) = stateHistory[steps]
                addPipes = False
            elif steps > 100:
                restartGame = False

        if not replayGame and addPipes:
             # 移动管道，管道在横轴方向移动
            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                uPipe["x"] += pipeVelX
                lPipe["x"] += pipeVelX

           # 第一个管道即将触及屏幕左侧时添加新管道
            if 0 < upperPipes[0]["x"] < 5:
                newPipe = getRandomPipe()
                upperPipes.append(newPipe[0])
                lowerPipes.append(newPipe[1])

            # 如果管道跑出了屏幕，移除管道
            if upperPipes[0]["x"] < -IMAGES_INFO["pipe"][WIDTH]:
                upperPipes.pop(0)
                lowerPipes.pop(0)

        if MODE not in [Mode.TRAIN_NOUI, Mode.TRAIN_REPLAY] or (MODE == Mode.TRAIN_REPLAY and (restartGame or replayGame)):
            # 绘制背景
            SCREEN.blit(IMAGES["background"], (0, 0))
            # 然后绘制管道
            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                SCREEN.blit(IMAGES["pipe"][0], (uPipe["x"], uPipe["y"]))
                SCREEN.blit(IMAGES["pipe"][1], (lPipe["x"], lPipe["y"]))
            #然后绘制地面
            SCREEN.blit(IMAGES["base"], (basex, BASEY))
            # 打印分数, score: int, 在游戏画面上显示分数
            showScore(score)
            # 把小鸟也画到游戏上，playerx, playery代表小鸟的位置
            SCREEN.blit(IMAGES["player"][playerIndex], (playerx, playery))
            if MODE == Mode.TRAIN_REPLAY:
                showDebugInfo(playerx, playery, playerVelY, lowerPipes)
            #更新下pygame的游戏画面
            pygame.display.update()
            FPSCLOCK.tick(FPS)

import matplotlib.pyplot as plt
#from matplotlib.ticker import MaxNLocator
def showPerformance():
    average = []
    num = 0
    sum_s = 0

    for s in SCORES:
        num += 1
        sum_s += s
        average.append(sum_s/num)

    print("\nEpisode: {}, highest score: {}, average: {}".format(num, max(SCORES), average[-1]))
    plt.figure(1)
    #plt.gca().get_xaxis().set_major_formatter(MaxNLocator(integer=True))
    plt.scatter(range(1, num+1), SCORES, c="green", s=3)
    plt.plot(range(1, num+1), average, 'b')
    plt.xlim((1,num))
    plt.ylim((0,int(max(SCORES)*1.1)))

    plt.title("Score distribution")
    plt.xlabel("Episode")
    plt.ylabel("Score")
    plt.show()

def showGameOverScreen(crashInfo):
    """
    游戏结束
    :param crashInfo:
    :return:
    """
    updateQtable(crashInfo["score"])
    if MODE != Mode.NORMAL and MODE != Mode.PLAYER_AI:
        return
    # 使player crashed并显示游戏结束画面
    score = crashInfo["score"]
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo["y"]
    playerHeight = IMAGES["player"][0].get_height()
    playerVelY = crashInfo["playerVelY"]
    playerAccY = 2

    basex = crashInfo["basex"]

    upperPipes, lowerPipes = crashInfo["upperPipes"], crashInfo["lowerPipes"]

    # 播放hit和die的声音
    SOUNDS["hit"].play()
    if not crashInfo["groundCrash"]:
        SOUNDS["die"].play()

    gameoverx = int((SCREENWIDTH - IMAGES["gameover"].get_width()) / 2)
    gameovery = int(SCREENHEIGHT * 0.4)

    while True:
        # 取消激活的按压键functionality
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if playery + playerHeight >= BASEY - 1:
                    return
        
        #return
        # 必须移除才能激活按键functionality

        # player y shift
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        # player 速度变化
        if playerVelY < 15:
            playerVelY += playerAccY

        # draw sprites
        SCREEN.blit(IMAGES["background"], (0, 0))

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES["pipe"][0], (uPipe["x"], uPipe["y"]))
            SCREEN.blit(IMAGES["pipe"][1], (lPipe["x"], lPipe["y"]))

        SCREEN.blit(IMAGES["base"], (basex, BASEY))
        showScore(score)
        SCREEN.blit(IMAGES["player"][1], (playerx, playery))
        SCREEN.blit(IMAGES["gameover"], (gameoverx, gameovery))

        FPSCLOCK.tick(FPS)
        pygame.display.update()


def playerShm(playerShm):
    """
    使playerShm['val']的值在8和-8之间摆动。
    :param playerShm:
    :return:
    """
    if abs(playerShm["val"]) == 8:
        playerShm["dir"] *= -1

    if playerShm["dir"] == 1:
        playerShm["val"] += 1
    else:
        playerShm["val"] -= 1

def getRandomPipe():
    """返回一组随机生成的管道，上下管道"""
    # 上下管之间的间隙是 y， gapY是 随机的0到，地面和 管道上部和下部之间的间隙 的一个随机值
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES_INFO["pipe"][HEIGHT]
    pipeX = SCREENWIDTH + 10

    return [
        {"x": pipeX, "y": gapY - pipeHeight},  # 上面的管道
        {"x": pipeX, "y": gapY + PIPEGAPSIZE},  # 下面的管道
    ]


def showScore(score):
    """
    在屏幕中心显示得分
    :param score: 分数  int
    :return:
    """
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0  # 要打印的所有数字的总宽度
    # scoreDigits里面进有一个数字时，例如0分，那么需要的显示宽度为： 24
    for digit in scoreDigits:
        totalWidth += IMAGES["numbers"][digit].get_width()
    #分数的位置
    Xoffset = (SCREENWIDTH - totalWidth) / 2
    #把分数画到游戏上
    for digit in scoreDigits:
        SCREEN.blit(IMAGES["numbers"][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES["numbers"][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """
    如果player与地面或管道相撞，则返回True。
    :param player: player信息 eg: {'x': 57, 'y': 244, 'index': 0, 'w': 34, 'h': 24}
    :param upperPipes: 上面管道 [{'x': 488, 'y': 198}, {'x': 632.0, 'y': 219}]
    :param lowerPipes: 下面管道 [{'x': 488, 'y': -222}, {'x': 632.0, 'y': -201}]
    :return:如果玩家撞到地面,[True, True],撞到管道[True, False]，没有撞到任何东西[False, False]
    """
    pi = player["index"]
    player["w"] = IMAGES_INFO["player"][0][WIDTH]
    player["h"] = IMAGES_INFO["player"][0][HEIGHT]

    # 如果玩家撞到地面
    if (player["y"] + player["h"] >= BASEY - 1) or (player["y"] + player["h"] <= 0):
        return [True, True]
    else:
        #创建一个Rect对象
        playerRect = pygame.Rect(player["x"], player["y"], player["w"], player["h"])
        # 管道的宽和高
        pipeW = IMAGES_INFO["pipe"][WIDTH]
        pipeH = IMAGES_INFO["pipe"][HEIGHT]

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # 创建上和下的管道rect对象
            uPipeRect = pygame.Rect(uPipe["x"], uPipe["y"], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe["x"], lPipe["y"], pipeW, pipeH)

            # 小鸟和上下管道的bool值的对象位置hitmasks， pHitMask（ 34，24），uHitmask 和lHitmask（52， 320）
            pHitMask = HITMASKS["player"][pi]
            uHitmask = HITMASKS["pipe"][0]
            lHitmask = HITMASKS["pipe"][1]

            # 是否小鸟和上下管道相撞，返回bool值，eg: uCollide: False
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)
            #如果任何一个相撞了，那么返回
            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """
    判断2个目标是否相撞，而不是仅仅通过他们的Rects矩阵范围判断
    :param rect1: <rect(57, 244, 34, 24)>， 这个例子宽和高为34和24
    :param rect2: <rect(488, -153, 52, 320)>
    :param hitmask1: bool shape (34,24)
    :param hitmask2: bool shape (52,320)
    :return:
    """
    #一个矩形和另一个矩形相减，看是否重叠, eg: <rect(57, 244, 0, 0)>, 这个例子宽和高都为0
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def getHitmask(image):
    """
    使用图像的alpha返回一个hitmask。即物体的像素的形状的bool值
    :param image: <Surface(52x320x32 SW)>, 图像的宽度是52
    :return:
    """
    # mask存储在图像每个宽和高的像素点的最后一个维度 image.get_at((x, y))--> (255, 255, 255, 0)的信息，如果为0，那么就为False, 否则为True, 应该判断的是不是有障碍物
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask


if __name__ == "__main__":
    main()
