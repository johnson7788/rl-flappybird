import json
import random


class Bot(object):
    """
    将Qlearning逻辑应用到Flappy bird游戏的Bot类。
    每次迭代后（迭代=1, 以鸟儿死亡结束的游戏）更新Q值。
    """

    def __init__(self):
        self.gameCNT = 0  # 当前运行的游戏次数，每次死亡后递增。
        self.discount = 1.0  #折扣因子
        self.r = {0: 0, 1: -1000}  # 奖励函数
        self.lr = 0.7   #学习率
        self.load_qvalues()  #从json文件加载q值
        self.last_state = "0_0_0_0" # 初始位置，必须不是任何其他可能的状态之一。
        self.initStateIfNull(self.last_state)
        self.last_action = 0
        self.moves = []
        #是否显示更多日志
        self.verbose = True

    def load_qvalues(self):
        """
        从JSON文件中加载q值
        """
        self.qvalues = {}  # 加载的q值是个dict，里面包含31326个元素
        try:
            fil = open("data/qvalues.json", "r")
        except IOError:
            return
        #注意qvalues中代表的意思，例如一个元素 '420_-20_-9_0': [-455.5245159900492, -487.06834829873003, 214]
        # key表示的是一种小鸟此时状态，代表小鸟此时左上角x距离管道0x的距离是420， 小鸟的y于管道0的y的距离是-20，小鸟的垂直方向的速度是-9，小鸟y于管道1的距离是0
        # 值的3个元素表示的意思是小鸟的
        self.qvalues = json.load(fil)
        fil.close()

    def showStep(self, num, state, action, new_state):
        print("{0:5d}: ({1:15s}:{2:6d}, {3:1d}): {4:6.0f} => ({5:15s}): {6:6.0f}, {7:6.0f}, {8:6d}"
            .format(num+1, state, self.qvalues[state][2], action, self.qvalues[state][action],
                    new_state, self.qvalues[new_state][0], self.qvalues[new_state][1], self.qvalues[new_state][2]))

    def showSteps(self, steps):
        start = 0 if len(steps) < 51 else len(steps) - 50
        for num, step in enumerate(steps[start:]):
            state, action, new_state = step
            self.showStep(num, state, action, new_state)

    def act(self, x, y, vel, pipe):
        """
        选择关于当前状态的最佳行动 - 选择0（不要flap）以tie-break
        :param x: 小鸟的左上角的x
        :param y: 小鸟的左上角的y
        :param vel: 小鸟的垂直方向的速度
        :param pipe: 所有的管道位置
        :return: int 返回一个行动，0或1，表示飞或不飞
        """
        # eg:state: string:  '420_-30_-9_0' , 小鸟的x坐标和管道0的x坐标的差值, y的差值，y方向上小鸟的速度，pipe表示小鸟y方向上和pip1的差值
        state = self.get_state(x, y, vel, pipe)
        # 将经验添加到历史记录中
        self.moves.append(
            (self.last_state, self.last_action, state)
        )
        # 大于600万步时报错下q table
        self.save_qvalues()
        #根据当前的状态采取行动，行动一共2种，飞或不飞
        action = 0 if self.qvalues[state][0] >= self.qvalues[state][1] else 1
        #使用当前状态更新Last_State
        self.last_state = state  #
        self.last_action = action
        print(f"当前的state是: {state}, 当前采取的行动是{action}")
        return action

    def initStateIfNull(self, state):
        if self.qvalues.get(state) == None:
             self.qvalues[state] = [0, 0, 0]  # [Q of no action, Q of flap action, Num of enter]
             num = len(self.qvalues.keys())
             if num > 20000 and num % 1000 == 0:
                print("======== Total state: {} ========".format(num))
             if num > 30000:
                print("======== New state: {0:14s}, Total: {1} ========".format(state, num))

    def terminate_game(self):
        """
        终止游戏并保存Q值，鸟儿还活着。
        :return:
        """
        history = list(reversed(self.moves))
        for exp in history:
            state, act, new_state = exp
            self.qvalues[state][act] = (1-self.lr) * self.qvalues[state][act] + \
                                   self.lr * ( self.r[0] + self.discount*max(self.qvalues[new_state][0:2]) )
        self.last_state = "0_0_0_0" # initial position, MUST NOT be one of any other possible state
        self.last_action = 0
        self.moves = []
        self.gameCNT += 1

    def save_qvalues(self):
        """
            在游戏过程中保存Q值，鸟类仍然活着，只是为了减少内存消耗
        :return:
        """
        if len(self.moves) > 6_000_000:
            #历史记录，选取最后500万条状态记录，翻转后使用
            history = list(reversed(self.moves[:5_000_000]))
            #递归每个记录
            for exp in history:
                #上一个状态，上一个行动，产生的新的状态
                state, act, new_state = exp
                #self.r 是奖励函数，self.discount是折扣因子
                self.qvalues[state][act] = (1-self.lr) * self.qvalues[state][act] + \
                                       self.lr * ( self.r[0] + self.discount*max(self.qvalues[new_state][0:2]) )
            self.moves = self.moves[5_000_000:]

    def update_scores(self, printLogs=False):
        """
        通过对经验的迭代更新q值。
        :param printLogs:
        :return:
        """
        history = list(reversed(self.moves))

        # Q-learning score updates
        # 如果鸟儿在top管管中死亡，则flag为True，即碰到了上面的管道
        high_death_flag = True if int(history[0][2].split("_")[1]) > 120 else False

        t = 0
        last_flap = True    # penalty for last flap action
        for exp in history:
            t += 1
            state = exp[0]
            act = exp[1]
            new_state = exp[2]

            self.qvalues[state][2] += 1

            # Select reward
            if t <= 2:
                cur_reward = self.r[1]
                if act: last_flap = False
            elif (last_flap or high_death_flag) and act:
                cur_reward = self.r[1]
                high_death_flag = False
                last_flap = False
            else:
                cur_reward = self.r[0]

            self.qvalues[state][act] = (1-self.lr) * self.qvalues[state][act] + \
                                       self.lr * ( cur_reward + self.discount*max(self.qvalues[new_state][0:2]) )


        printLogs = False
        if printLogs: self.showSteps(self.moves)
        self.gameCNT += 1  # increase game count
        # 更新策略后清除历史记录
        self.moves = []

    def get_state(self, x, y, vel, pipe):
        """
        format:
            x0_y0_v_y1,  eg: 组成这个'420_-30_-9_0'，然后用initStateIfNull初始化

        (x, y): 小鸟的坐标，左上角的点的坐标
        x0: 小鸟的x坐标和管道0的x坐标的差值 [-50, ...]
        y0: diff of y to pipe0
        v: current velocity
        y1: pip1的y和小鸟的y的差值
        :return:
        """
        pipe0 = pipe[0]
        pipe1 = pipe[1]
        if x - pipe[0]["x"] >= 50:
            pipe0 = pipe[1]
            if len(pipe) > 2:
                pipe1 = pipe[2]

        x0 = pipe0["x"] - x
        y0 = pipe0["y"] - y
        if -50 < x0 <= 0:  
            y1 = pipe1["y"] - y
        else:
            y1 = 0

        if x0 < -40:
            x0 = int(x0)
        elif x0 < 140:
            x0 = int(x0) - (int(x0) % 10)
        else:
            x0 = int(x0) - (int(x0) % 70)

        if -180 < y0 < 180:
            y0 = int(y0) - (int(y0) % 10)
        else:
            y0 = int(y0) - (int(y0) % 60)

        #x1 = int(x1) - (int(x1) % 10)
        if -180 < y1 < 180:
            y1 = int(y1) - (int(y1) % 10)
        else:
            y1 = int(y1) - (int(y1) % 60)
        # '420_-30_-9_0'
        state = str(int(x0)) + "_" + str(int(y0)) + "_" + str(int(vel)) + "_" + str(int(y1))
        self.initStateIfNull(state)
        return state


    def dump_qvalues(self, force=False):
        """
        将q值转储到JSON文件中。
        :param force:
        :return:
        """
        if force:
            print("******** Saving Q-table(%d keys) to local file... ********" % len(self.qvalues.keys()))
            fil = open("data/qvalues.json", "w")
            json.dump(self.qvalues, fil)
            fil.close()
            print("******** Q-table(%d keys) updated on local file ********" % len(self.qvalues.keys()))
