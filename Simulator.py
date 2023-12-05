import numpy as np
from numpy import random


class Simulator:
    def __init__(self, distribution='CBR', queue_size=100, packet_limit=1000):
        self.packet_limit = packet_limit
        self.packets_served = 0
        self.clock = 0
        self.clients_in_queue = 0
        self.arrive_time = list()
        self.queue_busy = 0
        self.last_event_time = 0
        self.server_busy = 0
        self.status = 0
        self.spacing_time = 0
        self.total_lambda_cbr = 0
        self.number_of_lambda_cbr = 0
        self.total_lambda_poiss = 0
        self.number_of_lambda_poiss = 0
        self.total_mi = 0
        self.number_of_mi = 0
        self.number_of_delays = 0
        self.distribution = distribution
        self.queue_size = queue_size
        self.last_index_in_queue = 0
        self.total_delay = 0
        self.L = [6, 3]
        self.r = [0.3, 0.2]
        self.avg_lambda_poiss = 0
        self.avg_lambda_cbr = 0
        self.avg_serve_time = 0
        self.avg_queue_time = 0
        self.rho = 0
        self.simulation_percent = 0
        self.avg_server_busy = 0
        self.avg_queue_busy = 0
        self.poisson_packets = 0
        self.vsi = [0, 0, 0]
        self.rho_cbr = 0
        self.rho_poiss = 0
        self.A = [0, self.__generate_event(1), self.__generate_event(2)]  # lista czasow kolejnego zdarzenia dla kazdego typu
        self.A[0] = min(self.A[1], self.A[2]) + self.__generate_event(0)

    def __str__(self):
        return f'''
        Clock: {self.clock}
        Status: {self.status}
        Clients in queue: {self.last_index_in_queue}
        Last event time: {self.last_event_time}
        Number of delays: {self.number_of_delays}
        Total delay: {self.total_delay}
        Queue busy: {self.avg_queue_busy}
        Average waiting time: {self.avg_queue_time}
        Server busy: {self.avg_server_busy}
        Packets served: {self.packets_served}
        Average lambda CBR: {self.avg_lambda_cbr}
        Average lambda Poisson: {self.avg_lambda_poiss}
        Rho CBR: {self.rho_cbr}
        Rho Poisson: {self.rho_poiss}
        Average serve time (1/mi): {self.avg_serve_time}
        Poisson packets: {self.poisson_packets}
        ======================'''

    def __time_algorithm(self):
        minimum = min(self.A)
        self.clock = minimum
        return self.A.index(minimum)

    def __calculate_vs(self, event_type):
        if self.distribution == 'expo':
            L = np.random.exponential(scale=3)
        else:
            L = self.L[event_type-1]
        return max(self.spacing_time, self.vsi[event_type]) + L/self.r[event_type-1]

    def __generate_event(self, event_type):
        if event_type > 0: # klient przyszedl
            if event_type == 2:
                time_between_clients = round(random.exponential(scale=self.r[1]), 2)
                self.total_lambda_poiss += time_between_clients
                self.number_of_lambda_poiss += 1
            elif event_type == 1:
                time_between_clients = self.r[0]
                self.total_lambda_cbr += time_between_clients
                self.number_of_lambda_cbr += 1
            else:
                return

            return self.clock + time_between_clients  # scale = lamdba (intensywnosc naplywu)
        elif event_type == 0: # klient odszedl
            serving_time = round(np.random.exponential(scale=0.3), 2)  # scale = 1/mi
            self.total_mi += serving_time
            self.number_of_mi += 1
            return self.clock + serving_time

    def __pop_from_queue(self):
        self.arrive_time[0] = [float('inf'), (float('inf'), float('inf'))]
        self.last_index_in_queue -= 1
        self.arrive_time = self.arrive_time[1:] + [self.arrive_time[0]]

    def __event_algorithm(self, event_type):
        self.clients_in_queue = self.last_index_in_queue # liczba klientow w kolejce w poprzedniej iteracji
        self.queue_busy += (self.clock - self.last_event_time) * self.clients_in_queue  # obszar ponizej Q(t)
        self.server_busy += (self.clock - self.last_event_time) * self.status  # obszar ponizej B(t)
        if event_type > 0:
            vs = self.__calculate_vs(event_type)
            self.vsi[event_type] = vs
            if event_type == 2:
                self.poisson_packets += 1
            if self.status == 0: # przychodzi klient, a serwer wolny
                self.number_of_delays += 1  # liczba opoznien
                self.status = 1
            elif self.status == 1: # przychodzi klient, ale serwer zajety
                if self.last_index_in_queue < self.queue_size: # kolejka nie jest pelna
                    self.arrive_time.append([vs, (self.clock, event_type)])
                    self.last_index_in_queue += 1
                    self.arrive_time.sort()
                else:
                    print("Queue is full! Dropping packet...")
            self.A[event_type] = self.__generate_event(event_type)

        elif event_type == 0: # klient odszedl
            if self.last_index_in_queue == 0: # kolejka jest pusta
                self.A[0] = float('inf')
                self.status = 0
            elif self.last_index_in_queue > 0: # w kolejce sa klienci
                type_of_client = self.arrive_time[0][1][1]
                self.spacing_time = self.arrive_time[0][0]
                self.number_of_delays += 1  # liczba opoznien
                self.total_delay += self.clock - self.arrive_time[0][1][0]
                self.__pop_from_queue()
                self.A[event_type] = self.__generate_event(event_type)
            self.packets_served += 1
        self.last_event_time = self.clock  # czas ostatniego zdarzenia

    def start_simulation(self):
        print("Simulation in progress...")

        while self.packets_served < self.packet_limit:
            event_type = self.__time_algorithm()
            self.__event_algorithm(event_type)
            if self.clock != 0:
                self.avg_lambda_cbr = self.total_lambda_cbr / self.number_of_lambda_cbr
                self.avg_lambda_poiss = self.total_lambda_poiss / self.number_of_lambda_poiss
                self.avg_serve_time = self.total_mi / self.number_of_mi
                self.avg_queue_time = self.total_delay / self.number_of_delays
                self.rho_cbr = self.avg_lambda_cbr * self.avg_serve_time
                self.rho_poiss = self.avg_lambda_poiss * self.avg_serve_time
                self.avg_queue_busy = self.queue_busy / self.clock
                self.avg_server_busy = self.server_busy / self.clock
            last = self.simulation_percent
            self.simulation_percent = round(self.packets_served / self.packet_limit * 100, 0)
            if self.simulation_percent != last:
                print(f"{self.simulation_percent}%")
        print(f'Poisson: {random.poisson(lam=self.clock)}')
        print("Simulation completed.")
        print(self)


if __name__ == "__main__":
    sim = Simulator(packet_limit=100)
    sim.start_simulation()
