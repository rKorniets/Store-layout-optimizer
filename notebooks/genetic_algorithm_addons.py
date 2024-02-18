def evaluate_layout(layout, check, start_pos=None, use_item_count=False, reward_type='max'):
    try:
        res = layout.get_check_optimal_path(check, start_point=start_pos, use_product_count=use_item_count)
    except Exception as e:
        #print(e)
        if reward_type == 'max':
            return 0, True
        else:
            return 999, True

    return len(res), False

def thread_func(t_layout, t_check_arr, t_start_pos, use_item_count):
    t_res = (0, 0)
    for check in t_check_arr:
        t = evaluate_layout(t_layout, check[1], t_start_pos, use_item_count=use_item_count)
        inc = 1 if t[1] else 0
        t_res = (t_res[0] + t[0], t_res[1] + inc)
    return t_res, t_layout