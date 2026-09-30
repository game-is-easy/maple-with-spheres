import time

from scripts.src.ocr import ocr_inv_bg_fg
from scripts.comboKeys import short_press, exec_key_sequence, multi_press, KEY_SPACE, PRL
from scripts.locate_im import screengrab
import subprocess


LINES_REGION = (550, 746, 500, 150)
PERCENT_CONVERSION_RATIO = 10  # 1% = 10


def get_potential_image(im_name=None):
    return screengrab(im_name, region=LINES_REGION)


def get_potential_lines(img):
    # img = screengrab("test6.png", region=LINES_REGION)
    return ocr_inv_bg_fg(img)


def fill_spaces(score):
    return str(score) + " " * (5 - len(str(score)))


def rate_potential_line(line, rating_rule, attempts=3):
    for attr in rating_rule:
        if line.startswith(attr):
            value = line[len(attr)+1:].strip().replace('+', '')
            if value.endswith('%'):
                if value[:-1].isdigit():
                    return int(value[:-1]) * PERCENT_CONVERSION_RATIO * rating_rule[attr]
            if value.isdigit():
                return int(value) * rating_rule[attr]
        if attr in line:
            time.sleep(0.2)
            return rate_potential_line(line, rating_rule, attempts-1) if attempts > 0 else 100
    return 0


def calc_total_score(potential_lines, rating_rules):
    scores = []
    for _ in rating_rules:
        scores.append(0)
    total_indent = max(map(lambda line: len(line), potential_lines))
    for line in potential_lines:
        values = []
        for i, rating_rule in enumerate(rating_rules):
            values.append(round(rate_potential_line(line, rating_rule), 1))
            scores[i] += values[i]
        indent = total_indent - len(line)
        print(f"{line}{' ' * indent} --> score + {' | '.join(map(fill_spaces, values))}")
    print(f"{' ' * (total_indent-1)}total score : {' | '.join(map(fill_spaces, scores))}\n")
    return scores


def roll(rating_rules, target_scores, max_n_rolls=9999, n_rolled=0, dmt_not_apply=False):
    seq = short_press(KEY_SPACE, delay_after_rep=2, execute=False)
    seq.extend(short_press(KEY_SPACE, delay_after_rep=2, execute=False))
    if dmt_not_apply:
        seq.extend(multi_press(PRL["ENTER"], delay_after_rep=10, execute=False))
    else:
        seq.extend(short_press(KEY_SPACE, delay_after_rep=10, execute=False))
    if type(target_scores) == list:
        assert len(target_scores) == len(rating_rules)
    else:
        target_scores = [target_scores] * len(rating_rules)
    for n_rolls in range(max_n_rolls):
        img = get_potential_image("test_im.png")
        potential_lines = get_potential_lines(img)
        scores = calc_total_score(potential_lines, rating_rules)
        for i, score in enumerate(scores):
            if score >= target_scores[i]:
                subprocess.run(['say', 'High score.'])
                return n_rolls + n_rolled
        exec_key_sequence(seq)


if __name__ == '__main__':
    import cv2
    # print(get_potential_lines(get_potential_image()))
    # potential_image = cv2.imread("test3.png")
    # potential_lines = get_potential_lines(potential_image)
    #
    rating_rule_int = {"INT": 1, "Magic ATT": 3.5, "LUK": 0.1, "All Stats": 1.1}
    rating_rule_luk = {"LUK": 1, "Attack Power": 3.5, "DEX": 0.1, "All Stats": 1.1}
    rating_rule_str = {"STR": 1, "Attack Power": 3.5, "DEX": 0.1, "All Stats": 1.1}
    rating_rule_dex = {"DEX": 1, "Attack Power": 3.5, "STR": 0.1, "All Stats": 1.1}
    rating_rule_att = {"Attack Power": 1}
    rating_rules = [
        rating_rule_str,
        rating_rule_dex,
        rating_rule_luk,
        rating_rule_int,
        # rating_rule_att,
    ]
    # target_scores = [100,70,100,100]
    target_scores = 60
    #
    # calc_total_score(potential_lines, rating_rules)
    n_rolls = roll(rating_rules, target_scores, 500, n_rolled=449, dmt_not_apply=False)
    print(f"rolled {n_rolls} times.")

