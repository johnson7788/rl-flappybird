
# 使用强化学习来训练一只永远不死的飞鸟。 

### [Use reinforcement learning to train a flappy bird NEVER to die](https://towardsdatascience.com/use-reinforcement-learning-to-train-a-flappy-bird-never-to-die-35b9625aaecc)

### [Video](https://youtu.be/PZ5YEKlKz80)  

![always flying](res/307K_flying.gif)

---

## 依赖包

Install **pygame 1.9.6** package first  
Install **python 3.7**

---

## File Structure

- `src/bot.py` - 这个文件包含了应用Q-Learning逻辑到游戏中的`Bot`类。

- `src/flappy.py` - python中的主程序文件，玩游戏或训练agent玩游戏。

- `data/qvalues.json` - Q-Learning中的状态动作表，通过删除此文件开始新的训练。

- `data/hitmasks_data.pkl` - 屏蔽数据以检测非UI训练模式下的崩溃。

---

## How to Run

``` dos
python3 src/flappy.py [-h] [--fps FPS] [--episode EPISODE] [--ai]
                      [--train {normal,noui,replay}] [--resume]
                      [--max MAX] [--dump_hitmasks]
```

- `-h, --help` : Show usage formation
- `--fps FPS` : number of frames per second, default value:
  - User play or normal training mode with UI: `25`
  - Replay training mode: `20`
  - AI play mode: `60`
- `--episode EPISODE` : Training episode number, default: 10,000
- `--ai` : AI play mode
- `--train {normal,noui,replay}` : Training mode:
  - `normal` : Normal training mode with UI
  - `noui` : Training without UI, fastest training mode
  - `replay` : Training without UI, replay game with UI from last 50 steps once the bird crashes, it provides a visual way to check how bird crashed.
- `--resume` : Resume game from last 50 steps before crash, it's useful to correct flying trajectory for rare scenario. But it's 3x slower than normal mode. When in replay training mode, this option is enabled automatically.  
- `--max MAX` : Maxium score per episode, restart game if agent reach this score, default: 10,000,000
- `--dump_hitmasks` : dump hitmasks to file and exit

### Play game in user mode

``` dos
python3 src/flappy.py
```

### 训练agent机器人不需要UI，玩1000次

``` dos
python3 src/flappy.py --train noui --episode 1000
```

### 训练agent机器人，replay在crashed中的最后50步，当鸟儿达到1000分时，重启新游戏。 

``` dos
python3 src/flappy.py --train replay --episode 1000 --max 1000
```

---

## Achievements

经过长时间的训练（10多个小时），我在**最大得分=10M**，**Episode=2**的情况下进行了验证测试。一旦鸟儿达到10M分，游戏就会重新开始。这个测试证明了训练后的agent可以长时间飞行，而不会出现任何崩溃。即使在没有UI的情况下进行训练，在我的Mac中也需要近2小时才能达到10M的分数。我在这个测试中只运行了2 episodes。

<p align="center">
<img src="res/episode_2_max_10M.png" width="430">&nbsp; &nbsp;
<img src="res/episode_2_max_10M_2.png" width="500"><br>
<b>Total episode: 2, Max score: 10,000,000</b></p>  

从起点到第一个柱子，鸟儿会在没有任何障碍物的情况下飞很长一段距离，第一根柱子前的状态不会和下面的训练一样，接下来的测试证明训练过的agent完美的处理了开始的旅程。设置**最大得分=10**，**episode=100000**，agent顺利通过测试。

<p align="center">
<img src="res/episode_100K_max_10_1.png" width="430">&nbsp; &nbsp;
<img src="res/episode_100K_max_10_2.png" width="500"><br>
<b>Total episode: 100,000, Max score: 10</b></p>  

第3次测试证明了任何一款游戏的稳定性和可重复性。在本次测试中，**最大得分=10000**，**episode=2000**，经过训练的agent也顺利通过。

<p align="center">
<img src="res/episode_2K_max_10K_1.png" width="430">&nbsp; &nbsp;
<img src="res/episode_2K_max_10K_2.png" width="490"><br>
<b>Total episode: 2,000, Max score: 10,000</b></p>

我做了最后的测试，看看鸟儿能飞多少分，只是为了好奇。我设置了**最大得分=50000000**，只有一个Episode。

<p align="center">
<img src="res/50M_Score.png" width="600"></p>

## Conclusion

**The trained agent(flappy bird) NEVER dies.**

---

## Background

Thanks [Cihan Ceyhan](https://github.com/chncyhn/flappybird-qlearning-bot) for providing a good example to start with. And much appreciated of [Sarvagya Vaish](https://github.com/SarvagyaVaish) explaining the theory in details [here](https://sarvagyavaish.github.io/FlappyBirdRL/).

在[Cihan Ceyhan](https://github.com/chncyhn/flappybird-qlearning-bot)的代码中，训练后的agent可以达到5000分以上，如下图。

<p align="center">
<img src="https://camo.githubusercontent.com/acc74a82be4f1a06bb3ee87dc68b57459f9d3613/687474703a2f2f692e696d6775722e636f6d2f45335679304f522e706e67" width="500"><br>
<a href="https://github.com/chncyhn/flappybird-qlearning-bot">Source: Flappy Bird Bot using Reinforcement Learning</a>
</p>  

不过大家也看到了，小鸟在每一局中都不能达到很高的分数，可能在任何分数都会崩溃。不够稳定。

### Is it possible to train a bird never to die in any game?

---

## How to Improve

### State Space

In [Sarvagya](https://github.com/SarvagyaVaish)'s post, 他定义了三个维度来表示一个状态。

- **X** - 到下一个管道的水平距离
- **Y** - 到下一个管道的垂直距离
- **V** - 鸟儿的当前速度

在[Cihan Ceyhan](https://github.com/chncyhn/flappybird-qlearning-bot)的代码中，如果鸟儿进入隧道超过30个像素(pipe宽度=52px)，鸟儿就会把眼睛移动到下一个pipe。但是，这可能会导致Q表的冲突结果。同样的X、Y、V（到下一个pipe），如果鸟儿的当前位置接近当前pipe的边部分（红色），鸟儿可能会坠入对鸟儿透明的隧道。

<p align="center">
<img src="res/X_Y_Distance.png" width="250">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  
<img src="res/Blind_In_Tunnel.png" width="250">
</p>

我在状态中增加了第四个维度。

- **`Y1`** - 是指下两根管子之间的垂直距离，根据连续两根管子的高度差，帮助鸟类提前采取行动。该值只在鸟类进入隧道部分时使用。它可以减少状态空间。

此外，鸟儿在隧道内50个像素长之前，仍然可以感知到当前的pipe。之后，鸟儿几乎飞出了隧道。刚刚通过的pipe已经无法影响到鸟儿了。是时候关注下一条pipe了。

<p align="center"><img src="res/X_Y_y1_distance.png" width="250"></p>

### Rewards in Q-learning  

经过以上改进，小鸟可以轻松飞到10000分。但是，还是不稳定，在达到10000分之前，会有很多失败。

正如[Sarvagya](https://github.com/SarvagyaVaish)所解释的那样，机器人每走一步都会得到**+1**的活着的奖励，而如果死了则会得到**-1000**的奖励。这在大多数情况下都很好用。

我们来看看下面的场景。下一个pipe比上一个pipe有很大的落差，游戏中两个pipe之间的最大垂直落差是142px。考虑到小鸟处于例子中显示的位置，如果小鸟在下落，想要成功通过这两个pipe，可能会走*路线1*或者*路线2*，但都不能成功通过下一个pipe。如果垂直落差没有达到最大落差的话，可能在大多数情况下都能成功。参考右图截图。

<p align="center">
<img src="res/Crash_at_high_pipe.png" width="250">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  
<img src="res/get_through_at_normal_case.png" width="250">
</p>

我们对鸟儿进行百万次训练，鸟儿积累了大量该位置的正值。最坏的情况是相当低的发生率，即使有一次导致崩溃的情况，**也只是减去1000个奖励**。剩余的数值仍然是一个很大的正值，或者说鸟儿可以很容易地从成功的训练中再获得1000个奖励。所以鸟儿一旦遇到类似的情况就会再次坠毁。

**`我把活着的奖励从1改成了0`**，这就迫使鸟儿专注于长期活着，远离任何导致死亡的行动。无论鸟儿过去成功跑了多少次，死亡时都会受到-1000奖励的惩罚。

**经过这次改进后，大大提高了稳定性。

### Resume Game from Death

很少遇到最坏的情况。换句话说，这只鸟对这些情况的训练次数不够。它可能遇到一次，但下一次，它不会遇到类似的情况。可能要花很长时间才能再次发生。

这对训练的来说是不理想的。我实时记录了小鸟旅程的最后50步，**`游戏可以从崩溃前的最后50步开始恢复`**。这对在短时间内穿越所有可能的状态有很大的帮助。

我们以前面的案例为例。小鸟在进入隧道时处于下降状态，无论它走*路线1*还是*路线2*或其他路线，都有可能在下一个管道上坠落，这时游戏重新开始，它可能会尝试其他动作而死亡。游戏从这时开始重启，它可能会尝试其他行动而死亡。再次重启游戏，直到鸟儿发现它应在上升状态下进入这个情况。然后，它可以通过任何情况，包括最坏的情况。

<p align="center"><img src="res/Correct_trajectory_at_high_pipe.png" width="250"></p>

### 内存问题

在 "Bot "类中，它保存了每次移动的状态信息，一旦鸟儿死亡，它就会用来更新Q表。

当鸟儿达到几百万分的时候，会消耗大量的内存。同时也降低了训练速度。

<p align="center"><img src="res/memory_before.png" width="500"></p>

每走500万步，相当于139,000个分数，我就更新Q表，然后减少array列表。我仍然留有100万步的缓冲区，以避免鸟儿在600万步后崩溃。

```python
def save_qvalues(self):
    if len(self.moves) > 6_000_000:
        history = list(reversed(self.moves[:5_000_000]))
        for exp in history:
            state, act, new_state = exp
            self.qvalues[state][act] = (1-self.lr) * self.qvalues[state][act] + self.lr * ( self.r[0] + self.discount*max(self.qvalues[new_state][0:2]) )
        self.moves = self.moves[5_000_000:]
```

改动后，最大内存消耗在1GB左右，比之前少了很多。

<p align="center"><img src="res/memory_after.png" width="500"></p>

### Q-table Initialization

在原方案中，它需要一个单独的步骤来初始化q表，而且它还包含了很多鸟儿从未经历过的状态。

在我的解决方案中，只有当鸟儿经历了一个新的状态时，状态才会被初始化。所以Q表只包含鸟儿曾经经历过的状态。而且不需要单独的步骤来先初始化Q-table。

如果要从头开始一个新的训练，只需要删除`data/`文件夹下的`qvalues.json`文件即可。

---

## 训练一只永不死的鸟的步骤

1. 设置 **Max score = 10K**, **Episode = 15K**, enable **resume** mode

``` dos
python3 src/flappy.py --train noui --episode 15000 --max 10000 --resume
```

<p align="center"><img src="res/episode_15K_max_10K.png" width="500"></p>  

2. Set **Max score = 10**, **Episode = 15K**, enable **resume** mode

``` dos
python3 src/flappy.py --train noui --episode 15000 --max 10 --resume
```

<p align="center"><img src="res/episode_15K_max_10.png" width="500"></p>  

3. 交替重复*`步骤1`*和*`步骤2`*，直到几乎所有的episodes都以理想的最高分结束。

<p align="center">
<img src="res/episode_1K_max_10K.png" width="400">
<img src="res/episode_100K_max_10.png" width="400">
</p>

4. 设置更高的**最大得分=10M**，**episode=1000**，启用**resume**模式，直到能达到10M的最大得分。

``` dos
python3 src/flappy.py --train noui --episode 1000 --resume
```

<p align="center"><img src="res/episode_2_max_10M_1.png" width="500"></p>  

5. 从头开始训练一只鸟到完美状态可能需要10多个小时。验证AI机器人没有**resume**选项，会快3倍。在我的Mac中达到10M的分数大约需要2小时。如果鸟儿在开始阶段一直遇到崩溃，请尝试在*`步骤2`*中训练更多的episode。如果鸟在后面阶段崩溃，尝试在*`步骤1`*中训练更多的episode。

---

## References

http://sarvagyavaish.github.io/FlappyBirdRL/  
https://github.com/chncyhn/flappybird-qlearning-bot  
https://github.com/sourabhv/FlapPyBird  

