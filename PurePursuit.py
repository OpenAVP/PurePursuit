# -*-coding:GBK-*-
import os.path

import numpy as np
from matplotlib import pyplot as plt

import runtime


# �Ƕȶ��õ��ǻ����ƣ�����


class PurePursuit:
    def __init__(self, lam=runtime.lam, c=runtime.c, L=runtime.L):
        self.lam = lam
        self.c = c
        self.L = L

    def one_step(self, ref_path: np.ndarray, ego_state: np.ndarray) -> np.ndarray:
        """
        1. ����Ԥ�����
        2. ��ref_path����һ��Ԥ��㣨Ŀǰ��򵥵�ʵ���У�����ref_path����һ��������ӽ�ld�ĵ㣩
        3. ����Ԥ���������ָ��
        :param ref_path: ((x,y)...)
        :param ego_state: (x,y,yaw,v)
        :return:
        """
        ## ����Ԥ�����
        ld = self.lam * ego_state[3] + self.c

        ## Ѱ��Ԥ���
        dis = np.linalg.norm(ref_path - ego_state[:2], 2, axis=1)
        start_idx = np.argmin(dis)
        dis = ld - dis

        dis[dis < 0] = float('inf')  ## �൱�ڸ��������ld��֮ǰ�ĵ�ĵ��mask
        dis[:start_idx] = float('inf')

        ref_point = ref_path[np.argmin(dis)]

        ## �������ָ��
        alpha = np.arctan2(ref_point[1] - ego_state[1], ref_point[0] - ego_state[0]) - ego_state[2]
        delta = np.arctan2(2 * self.L * np.sin(alpha), ld)
        return delta


# TODO: carla-test


class SimpleTest:
    class CarModel:
        def __init__(self, initial_state=np.array([0, 0, 0, 1]).astype(np.float), L=runtime.L, dt=runtime.dt):
            self.state = initial_state
            self.L = L
            self.dt = dt

        def update_state(self, accel, delta):
            self.state[0] = self.state[0] + self.state[3] * np.cos(self.state[2]) * self.dt
            self.state[1] = self.state[1] + self.state[3] * np.sin(self.state[2]) * self.dt
            self.state[2] = self.state[2] + self.state[3] / self.L * np.tan(delta) * self.dt
            self.state[3] = self.state[3] + accel * self.dt

    def __init__(self, initial_state=np.array([0, 0, -0.5 * np.pi, 1]).astype(np.float),
                 lam=runtime.lam, c=runtime.c, L=runtime.L, dt=runtime.dt):
        self.model = SimpleTest.CarModel(initial_state, L, dt)
        self.pure_pursuit = PurePursuit(lam, c, L)

    def offline_test(self, path, test_cnt, x_lim=runtime.x_lim, y_lim=runtime.y_lim,
                     result_dir=runtime.save_fig_dir,result_name = runtime.save_fig_name):
        if not os.path.exists(result_dir):
            os.mkdir(result_dir)
        save_path = os.path.join(result_dir,result_name)
        plt.xlim([-x_lim, x_lim])
        plt.ylim([-y_lim, y_lim])
        past = path[0]
        for idx, p in enumerate(path):
            if idx > 0:
                plt.plot([past[0], p[0]], [past[1], p[1]], c='black')
                past = p

        past_s = self.model.state
        for i in range(test_cnt):
            delta = self.pure_pursuit.one_step(path, self.model.state)
            self.model.update_state(0, delta)
            print(self.model.state)
            plt.plot([past_s[0], self.model.state[0]], [past_s[1], self.model.state[1]], c='red')
            past_s = self.model.state.copy()
        plt.savefig(save_path)
        plt.show()

    @staticmethod
    def simple_read(filename):
        with open(filename, 'r') as f:
            lines = f.readlines()
        path = []
        for l in lines:
            str_array = l.split('(')[1].split(')')[0].split(',')
            p = np.array([float(str_array[0]), float(str_array[1])])
            path.append(p)
        return np.array(path)
