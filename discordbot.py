import discord
import itertools
import re
import pandas as pd

# discord関連のsetup的なやつ
TOKEN = 'ODQxNzgxMTE4MTgwOTE3Mjc4.YJrvwg.6ApXyEuySyzIR3mHTB6hMzSIfQg'
client = discord.Client()
bot_id = 841784963821338664
Registration_ch = 841783127113465917
Matching_ch = 841783191735369736
Result_ch = 842236680978956288

# レーティング関連のやつ


class Player:
    def __init__(self, name='NoName', rating=1500, rate_num=0, rate_buf=0.):
        self.name = name
        self.rating = rating
        self.rate_num = rate_num
        self.rate_buf = rate_buf

    def win_probability(self, rival):
        return 1. / (10. ** ((rival.rating - self.rating) / 400.) + 1.)

    @property
    def K(self):
        measurement = 7  # 計測試合数の設定
        return 24 if self.rate_num >= measurement else 32


def rate(winner, loser,):
    winner_result = 1.
    loser_result = 0.
    # レート変化の計算
    # (4人分計算してからレート反映させるため差分のみで反映させない)
    new_winner_rating_dif = winner.rate_buf + winner.K * \
        (winner_result - winner.win_probability(loser))
    print(new_winner_rating_dif)
    new_loser_rating_dif = loser.rate_buf + loser.K * \
        (loser_result - loser.win_probability(winner))
    print(new_loser_rating_dif)

    # 格納
    new_winner = Player(name=winner.name, rating=winner.rating,
                        rate_num=winner.rate_num, rate_buf=new_winner_rating_dif)
    new_loser = Player(name=loser.name, rating=loser.rating,
                       rate_num=loser.rate_num, rate_buf=new_loser_rating_dif)
    print(new_winner.rate_buf)
    print(new_loser.rate_buf)
    return new_winner, new_loser,


players = {}  # idとレートのディクショナリ
# 既にあるデータの読み込み
rate_path = r'EloSqRating.csv'
df = pd.read_csv(rate_path, index_col='id')
csv_id = 0
csv_name = 1
csv_rating = 2
csv_num = 3
for row in df.itertuples():
    players[row[csv_id]] =\
        Player(name=row[csv_name], rating=row[csv_rating],
               rate_num=row[csv_num])


# その他変数
matching_flag = 0
team_num = 2
battle_member = []
best_team = []
return_val = None
# --------------------------------
# 関数関係


def calc_team_power(team):  # teamは4つのidが入ったリスト
    return sum([players[i].rating for i in team])


def make_team(battel_member):  # battle_memberはリスト型
    player1 = battel_member[:1]
    battel_member = battel_member[1:]
    min_dif = 10000
    best_team = []
    # 妥協の全数探索
    # 35通りだから許してください
    for i in itertools.combinations(battel_member, team_num // 2 - 1):
        alpha = player1 + list(i)
        beta = [j for j in battel_member if (j not in i)]
        team_dif = abs(calc_team_power(alpha) - calc_team_power(beta))
        if (min_dif > team_dif):
            min_dif = team_dif
            best_team = alpha + beta
    print(best_team)
    return best_team


# resultのメッセージがフォーマットに合致しているか判定する関数
def result_judge(team_num, msg_con):
    global return_val
    msg = 'result\s*winner'
    for i in range(team_num // 2):
        msg += '\s*<@!\d{18}>'
    msg += '\s*loser'
    for i in range(team_num // 2):
        msg += '\s*<@!\d{18}>'
    msg = 're.fullmatch(r\'' + msg + '\', \'' + msg_con + '\')'
    return_val = None
    msg = 'global return_val\nreturn_val = ' + msg
    print()
    print('↓↓↓↓↓↓↓↓↓受け取ったメッセージ')
    print(msg_con)
    print()
    print('↓↓↓↓↓↓↓↓↓比較対象のメッセージ↓↓↓↓↓↓↓↓↓↓↓↓')
    print(msg)
    print()
    exec(msg)
    print(return_val)
    if return_val:
        print('T')
    else:
        print('F')
    return return_val

# 結果をレートに反映させる関数


def reflect_rate(win_member, lose_member):
    # 各メンバーそれぞれに対して勝敗計算
    for winner_name in win_member:
        for loser_name in lose_member:
            winner = players[winner_name]
            loser = players[loser_name]
            new_winner, new_loser = rate(winner, loser)
            players[winner_name] = new_winner
            players[loser_name] = new_loser

    # まとめて各試合のレート計算を反映させる
    # データフレームの書き換え、csvの書き込みも行う
    for member in win_member + lose_member:
        players[member].rating += players[member].rate_buf
        players[member].rate_buf = 0
        players[member].rate_num += 1
        print(players[member].name, players[member].rating)
        # データフレームに書き込む
        df.loc[member, 'rating': 'rate_num'] = [
            players[member].rating, players[member].rate_num]
        print('\n---\n', df, '\n---\n')
        df.to_csv(rate_path, encoding='utf-8')


# --------------------------------

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    global players
    global df
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return

    # 登録チャンネルでの処理
    if message.channel.id == Registration_ch:
        # DMをつくる、プレイヤーリストに追加する
        if (message.content == '!registration') or (message.content == '!r'):
            print(message.author)
            A = message.author
            print(A)
            # playersにidが入っていなければ、追加処理をする
            if message.author.id not in players:
                name = message.author.name + '#' + message.author.discriminator
                players[message.author.id] = Player(name)
                print('not in')
                df.loc[message.author.id] = [
                    players[message.author.id].name, 1500., 0]
                print('\n---\n', df, '\n---\n')
                df.to_csv(rate_path, encoding='utf-8')
                await message.author.send('\
                    登録完了しました\n初期レートは1500です\n開始から7戦の間はブーストがかかります')
                await message.channel.send(f'{message.author.mention}さんにDMを送信しました')
            # playersにidが入っていたらえらー文を返す
            else:
                await message.channel.send(f'{message.author.mention}さんは既に登録済みです')
            print(players)

    # マッチングチャンネルでの処理
    elif message.channel.id == Matching_ch:
        global matching_flag
        global team_num
        global battle_member
        global best_team
        #!startの処理
        if (message.content == '!start'):
            # matching flagが0で募集が始まっていないとき
            if (matching_flag == 0):
                matching_flag = 1
                battle_member = [message.author.id]
                await message.channel.send(f'\
                    募集を開始しました\n\
                    現在@{team_num-len(battle_member)}')
            # matching flagが1で募集中の時
            else:
                await message.channel.send(f'\
                    既に募集中です\n\!canで参加できます\n\
                    現在@{team_num-len(battle_member)}')
        #!canの処理
        elif (message.content == '!can'):
            # 募集中の時
            if (matching_flag == 1):
                # 募集にまだ参加していなかったら
                if (message.author.id not in battle_member):
                    battle_member.append(message.author.id)
                    # 募集を締め切るかどうかの判定
                    if (len(battle_member) == team_num):
                        matching_flag = 0
                        print(battle_member)
                        # チーム分けの処理
                        best_team = make_team(battle_member)
                        print(best_team)
                        alpha = [
                            players[i].name for i in best_team[:team_num // 2]]
                        beta = [
                            players[i].name for i in best_team[team_num // 2:]]
                        await message.channel.send(f'\
                            {team_num}人集まりました、チーム分けは以下の通りです\n\
                            alpha = {alpha}\n\
                            beta = {beta}')
                    # まだ募集を締め切らないとき
                    elif (len(battle_member) < team_num):
                        await message.channel.send(f'\
                            参加処理ができました\n\
                            現在@{team_num-len(battle_member)}')
                    # ラグか何かよくわからないけど人数超えちゃったとき
                    else:
                        await message.channel.send('マッチング人数エラー')
                # 参加しようとしたけど既に参加していた時
                elif (message.author.id in battle_member):
                    await message.channel.send(f'{message.author.mention}さんは既に参加済みです\n\
                        現在@{team_num-len(battle_member)}')
            # 募集が開始していなかった時
            else:
                await message.channel.send('現在募集していません')
        # dropの処理
        elif (message.content == '!drop'):
            # 募集しているとき
            if (matching_flag == 1):
                # 募集にその人が既に参加しているとき
                if (message.author.id in battle_member):
                    battle_member.remove(message.author.id)
                    # この離脱で待機人数がいなくなったら募集を終わらせる
                    if (len(battle_member) == 0):
                        matching_flag = 0
                        await message.channel.send(f'参加者がいなくなったので募集を中止します')
                    # まだ人が残るようなら
                    else:
                        await message.channel.send(f'参加取り消し処理ができました\n\
                            現在@{team_num-len(battle_member)}')
                # 募集にその人が参加していなかった時
                else:
                    await message.channel.send(f'{message.author.mention}さんは参加していません')
            # 募集が始まっていなかった時
            else:
                await message.channel.send('現在募集していません')
        # memberの処理
        elif (message.content == '!member'):
            # 募集中の時
            if (matching_flag == 1):
                msg = ''
                for i in battle_member:
                    msg += players[i].name + ', '
                await message.channel.send(f'\
                    現在のメンバー\n{msg}')
            # 募集していなかった時
            else:
                await message.channel.send('現在募集していません')

    # 結果送信チャンネルでの処理
    elif message.channel.id == Result_ch:
        # 送られてきた文字列が結果のフォーマットに合っているかの判定
        print(message.content)
        return_val = result_judge(team_num, message.content)
        if return_val:  # パターンマッチのやつ醜いので関数にまとめました
            print('パターンにマッチしました')
            result_member = re.findall(r'\d{18}', message.content)
            result_member = [int(i) for i in result_member]
            print('----------------------------------')
            print('result_member', result_member)
            print('players', players)
            print('----------------------------------')
            win_member = result_member[:len(result_member) // 2]
            lose_member = result_member[len(result_member) // 2:]
            reflect_rate(win_member, lose_member)
            await message.channel.send('結果の反映が完了しました')
        else:
            await message.channel.send('フォーマットにマッチしません')

    # DMでの処理
    elif isinstance(message.channel, discord.DMChannel):
        if message.content == '!rate':
            print(players[message.author.id])
            await message.channel.send(f'あなたのレートは{players[message.author.id].rating:.1f}です')


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
