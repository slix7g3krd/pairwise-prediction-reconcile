"""第 58 批：客户端预测与服务器校正的核心工具函数。

覆盖 tick 对齐、丢包重放、全状态回滚、延迟补偿、载具绑定、预测碰撞、
时钟同步、输入去重、自适应校正阈值以及快照键等基础能力。
"""

def tick_rate(client_hz, server_hz):
    """返回服务器与客户端 tick 比。

    客户端预测以 client_hz 推进，服务器权威状态以 server_hz 推进。
    比值用于把客户端帧映射到服务器 tick 上，避免同一帧输入被应用两次。
    """
    if client_hz <= 0:
        raise ValueError("client_hz 必须为正数")
    return server_hz / client_hz

def replay_count(inputs, lost):
    """返回重放输入数量。

    丢包时服务器确认停留在更早的 tick，需要把本地全部未确认输入重放；
    未丢包时最新一帧已随包发送，只需重放其之前的输入。
    """
    if lost:
        return len(inputs)
    return max(len(inputs) - 1, 0)

def rollback_state(state, snapshot):
    """回滚到快照。

    返回快照的浅拷贝，保证回滚覆盖位置、冷却、弹药、载具油量等全部状态，
    而不是只回滚位置字段。
    """
    return dict(snapshot)

def lag_compensation(rtt, max_comp):
    """返回延迟补偿上限。

    单程延迟约为 rtt/2，且不超过 max_comp，避免把其他玩家倒带得过远。
    """
    return min(rtt / 2.0, max_comp)

def bind_vehicle(player_pos, vehicle_pos):
    """绑定角色与载具状态。

    角色进入载具后两者作为同一权威实体一起回滚，返回绑定后的联合状态。
    """
    return (tuple(player_pos), tuple(vehicle_pos))

def predict_collision(next_pos, wall):
    """预测碰撞。

    客户端预测同样需要做碰撞检测：目标位置到达或越过墙体即视为碰撞。
    """
    return next_pos <= wall

def clock_offset(server_time, client_time):
    """返回时钟偏移。

    以服务器时间为基准，偏移 = 服务器时间 - 客户端时间。
    """
    return server_time - client_time

def dedupe_inputs(seqs):
    """按序号去重。

    返回升序排列的唯一序号，避免快速连点时同一输入被放大。
    """
    return sorted(set(seqs))

def correct_threshold(drift, base):
    """返回自适应校正阈值。

    漂移越大阈值越宽松（2 倍漂移），但下界不低于基础阈值，
    使慢速增长的小漂移最终也会被纠正。
    """
    return max(base, drift * 2)

def snapshot_key(tick, version):
    """返回快照键。

    键中同时包含 tick 与协议版本，便于版本升级后区分快照结构。
    """
    return f"{tick}:{version}"
