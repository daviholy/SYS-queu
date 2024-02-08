from numpy import random
import simpy
import math
import matplotlib.pyplot as plt
import pandas as pd
from enum import Enum
from numpy.random import lognormal
from collections import namedtuple

simTime = 860  # for how long run the simulation (simpy internal time)
openHour = 10  # opening hour of the supermarket
closeHour = 19  # closing hour of the supermarket
totalCloseHour = (
    20  # hour when the shop should be totally closed (ie. without any people in it)
)
MaMinimal = 20  # number of men in least busy hour
FeMinimal = 30  # number of women in least busy hour
tolerablequeue = 20  # maximal tolerable length of queuee for people
tick = 1  # how much will be called time.update ( progress time by 1 minute) per internal time
sampling = 2  # sample rate ( time interval between samples)
cashiers = 4  # number of maximal opened cashiers
max_length = 10  # maximal length of que by cashier, for opening next cashier
min_length = 2  # minimal length for cashier to close it
maxPay = 50  # maximal amount of pay customer can pay
minTime = 20  # minimal time for which cashdesk must stay opened
newMinTime = 10  # minimal time between opening new cashdesk

# data obtained from the analysis of the dataframe
data = pd.DataFrame(
    {
        "MaStd": [
            0.816886097075351,
            0.970839853974609,
            0.9569378865756415,
            0.8971273356756472,
            1.0633629472000017,
            1.0303366308528283,
            0.851591369839412,
            0.8401247066712134,
            0.8219971126003871,
            0.9127900876837194,
        ],
        "MaMean": [
            2.5799895310346925,
            2.528125768907977,
            2.0688860277403194,
            2.315635050273642,
            2.7820906921718276,
            2.4505158613645253,
            2.4635553238769647,
            2.286638003061921,
            2.3318789320271236,
            2.5207563026816975,
        ],
        "MaDiff": [
            1.0833333333333333,
            1.1944444444444444,
            1.1944444444444444,
            1.1666666666666667,
            1.2222222222222223,
            1.6666666666666667,
            1.1388888888888888,
            1.0,
            1.3333333333333333,
            1.6388888888888888,
        ],
        "FeMean": [
            2.291791934431301,
            2.442173107201099,
            2.367176498297674,
            2.644790861463019,
            2.6611682152020797,
            2.4080882085652036,
            2.7614959526513303,
            2.6440569185714105,
            2.220561257515455,
            2.808566934110506,
        ],
        "FeStd": [
            0.9659905441431078,
            0.9803369008546821,
            0.9324330507100937,
            0.8315689573780449,
            0.9854706448025854,
            1.0577016149355032,
            0.6966283636181579,
            0.9035367098565192,
            1.0449770526788893,
            0.8355394169843695,
        ],
        "FeDiff": [
            1.7222222222222223,
            1.3055555555555556,
            1.2777777777777777,
            1.6944444444444444,
            1.0833333333333333,
            1.1666666666666667,
            1.0,
            1.0555555555555556,
            1.25,
            1.5,
        ],
    }
)


class Gender(Enum):
    """
    represents Gender of customer in store
    """

    Male = 1
    Female = 2


class Time:
    """
    represent actual time in the simulation
    """

    def __init__(self, env):
        self.hour = openHour
        self.minute = 0
        self.env = env
        self.day = 0

    def update(self):
        """
        forward the time by 1 minute or proceed to the next day
        """
        self.minute = self.minute + 1
        while self.minute >= 60:
            self.minute = self.minute - 60
            self.hour = self.hour + 1
            break
        if self.hour >= totalCloseHour:
            self._open()

    def _open(self):
        """
        check if the store is empty,if it's not, raise exception else proceed to next day and set the time to open hour
        """
        if self.env.total_total != 0:
            raise ValueError("The supermarket isn't empty after closing time")
        if (
            ((closeHour - openHour + 1) * 60) % sampling
        ) != 0:  # check if we have last sample at the closing hour, if not take the sample
            try:
                self.env.collector.collect()
            except:
                pass
        self.hour = openHour
        self.minute = 0
        self.env.newDay()
        self.day = self.day + 1

    def print(self):
        """
        return actual time
        :return: formatted string with the time
        """
        return f"{self.day}.{self.hour}:{self.minute}"


class Environment(simpy.Environment):
    """
    enhanced Basic simpy.Environment for logging in 3 levels differentiated with different colors
    basic: just logging information
    Warning: crucial information's
    error: State in which simulation can't continue and need to be corrected
    By default all 3 logging levels are enabled
    """

    def __init__(self, enabled=True, errorEnabled=True, warningEnabled=True):
        super().__init__()
        self.logEnabled = enabled
        self.errorLogEnabled = errorEnabled
        self.warningLogEnabled = warningEnabled

    def log_off(self, log=True, error=False, warning=False):
        """
        turn off the logging for specified levels
        :param log: toggle basic level
        :param error: toggle error level
        :param warning: toggle warning level
        """
        if log:
            self.logEnabled = False
        if error:
            self.errorLogEnabled = False
        if warning:
            self.warningLogEnabled = False

    def log_on(self, log=True, error=False, warning=True):
        """
        turn on the logging for specified levels
        :param log: toggle basic level
        :param error: toggle error level
        :param warning: toggle warning level
        """
        if log:
            self.logEnabled = True
        if error:
            self.errorLogEnabled = True
        if warning:
            self.warningLogEnabled = True

    def log(self, text, entity=None):
        """
        log the basic message. There's no any logging into file implemented it will just print message to standard output.
        :param text:
        :param entity:
        """
        if self.logEnabled:
            print(f"{self.now}: {text} {f'({entity})' if entity is not None else ''}")

    def errorLog(self, text, entity=None):
        """
        log the error message. There's no any logging into file implemented it will just print message to standard output, in red color using ANSI escape sequence.
        More about NASi escape characters: https://en.wikipedia.org/wiki/ANSI_escape_code#24-bit
        """
        if self.errorLogEnabled:
            print(
                f"{self.now}: \033[31;1m{text}\033[m \033[m {f'({entity})' if entity is not None else ''}"
            )

    def warningLog(self, text, entity=None):
        """
        log the warning message in the same way as error, but in yellow color
        """
        if self.warningLogEnabled:
            print(
                f"{self.now}: \033[33m{text}\033[m {f'({entity})' if entity is not None else ''}"
            )

    def registCollector(self, collector):
        """
        attach collector to the environment, so that it can be accessed by other objects from it.
        :param collector: collector to attach
        """
        self.collector = collector


class Shop(Environment):
    """
    represents the simulated shop. It stores customers and cashdesks.
    """

    def __init__(self, NumOfCashDesks):
        super().__init__()
        self.time = Time(self)
        self.total_women = 0
        self.total_men = 0
        self.total_total = 0
        self.totalIncome = 0
        self.menIncome = 0
        self.womenIncome = 0
        self.lostIncome = 0
        self.cashdesks = [CashDesk(self) for _ in range(NumOfCashDesks)]
        for p in self.cashdesks[1:]:
            p.close()

    def newDay(self):
        """
        prepare the store and cashdesks for the new day.
        """
        self.total_women = 0
        self.total_men = 0
        self.total_total = 0
        self.totalIncome = 0
        self.menIncome = 0
        self.womenIncome = 0
        self.lostIncome = 0
        for p in self.cashdesks:
            p.queue = []
            # clearing internal queuee of simpy.resources. This will lead to exceptions, when the still alive process
            # will try to remove yourself from the queuee, we need to catch it and suppress it.
            p.get_queuee = []
            p.put_queuee = []
            p.close()
        self.cashdesks[0].open()


class Entity:
    """
    base class, which stores environment
    """

    def __init__(self, env):
        self.env = env


class Collector(Entity):
    """
    base collector class, which they collect data from the environment
    """

    def __init__(self, env, interval):
        super().__init__(env)
        self.interval = interval
        if env is not None:
            self.env.registCollector(self)

    def collect(self):
        raise NotImplemented("abstract method")


class ShopStatistic(Collector):
    """
    collector, which takes samples from shop variables. Data are stored into list which represent days of simulation,
    income_cashiers have also another lists above list of days, which represents individual cashdesks
    """

    def __init__(self, env: Environment, interval):
        super().__init__(env, interval)
        simulatedDays = math.ceil(simTime / ((closeHour - openHour + 1) * 60))
        self.customer = [[] for _ in range(simulatedDays)]
        self.men = [[] for _ in range(simulatedDays)]
        self.women = [[] for _ in range(simulatedDays)]
        self.byCashDesk = [[] for _ in range(simulatedDays)]
        self.income_total = [[] for _ in range(simulatedDays)]
        self.income_women = [[] for _ in range(simulatedDays)]
        self.income_men = [[] for _ in range(simulatedDays)]
        self.income_cashiers = [
            [[] for _ in range(cashiers)] for i in range(simulatedDays)
        ]
        self.queuee_cashiers = [
            [[] for _ in range(cashiers)] for i in range(simulatedDays)
        ]
        self.lostMoney = [[] for _ in range(simulatedDays)]
        self.openedCashiers = [[] for _ in range(simulatedDays)]
        self.env.process(self.lifetime())

    def lifetime(self):
        """
        periodically takes samples in specified period
        """
        while True:
            self.collect()
            yield self.env.timeout(self.interval)

    def collect(self):
        """
        storing the data of actual simulation
        """
        self.customer[self.env.time.day].append(self.env.total_total)
        self.men[self.env.time.day].append(self.env.total_men)
        self.women[self.env.time.day].append(self.env.total_women)
        self.byCashDesk[self.env.time.day].append(
            sum(len(p.queue) for p in self.env.cashdesks)
        )
        self.income_total[self.env.time.day].append(self.env.totalIncome)
        self.income_men[self.env.time.day].append(self.env.menIncome)
        self.income_women[self.env.time.day].append(self.env.womenIncome)
        self.openedCashiers[self.env.time.day].append(
            len([_ for _ in self.env.cashdesks if _.isOpen])
        )
        self.lostMoney[self.env.time.day].append(self.env.lostIncome)
        [
            self.income_cashiers[self.env.time.day][x].append(
                self.env.cashdesks[x].income
            )
            for x in range(cashiers)
        ]
        [
            self.queuee_cashiers[self.env.time.day][x].append(
                len(self.env.cashdesks[x].queue)
            )
            for x in range(cashiers)
        ]


class CashDesk(simpy.Resource):
    """
    represents cashdesk in the shop. It receives payment and have queuee for customers
    """

    def __init__(self, env):
        super(CashDesk, self).__init__(env)
        self.isOpen = True
        self.queue = []
        self.resource = simpy.Resource(env, capacity=1)
        self.env = env
        self.income = 0
        self.timeOfOpen = env.now

    def open(self, openTime=0):
        """
        open the cashdesk
        """
        self.isOpen = True
        self.timeOfOpen = openTime

    def close(self):
        """
        close the cashdesk
        :return:
        """
        self.isOpen = False

    def pay(self, gender: Gender, amount):
        """
        receive the payment
        :param gender: gender of the customer
        :param amount: amount of money to pay
        """
        self.env.totalIncome += amount
        self.income += amount
        if gender == Gender.Male:
            self.env.menIncome += amount
        else:
            self.env.womenIncome += amount


class Customer(Entity):
    """
    represent the Customer in the store
    """

    def __init__(self, env: Shop, gender: Gender, shoppingDuration):
        super().__init__(env)
        self.shoppingDuration = shoppingDuration
        self.env.process(self.lifetime())
        self.gender = gender

    @staticmethod
    def get_lognormal(mean=0, sd=1):
        """
        helpful static method for getting random variable from lognormal
        :param mean: mean for the
        :param sd: standard deviation
        """
        tmp = lognormal(mean=mean, sigma=sd)
        while tmp > maxPay:
            tmp = lognormal(mean=mean, sigma=sd)
        return tmp

    @staticmethod
    def get_total_price(time: Time, gender: Gender):
        """
        generate the amount of cash for payment
        :param time: time object which represent actual time
        :param gender: gender of customer
        """
        try:
            if gender is Gender.Male:
                par = Customer.get_total_price.male[time.hour - openHour]
            else:
                par = Customer.get_total_price.female[time.hour - openHour]
            return Customer.get_lognormal(par.mean, par.std)
        except AttributeError:  # initialize the generators
            Customer.get_total_price.male = []
            Customer.get_total_price.female = []
            Parameters = namedtuple("Parameters", ["mean", "std"])
            # construct lists of generators
            for _ in range(openHour, closeHour + 1):
                Customer.get_total_price.male.append(
                    Parameters(
                        data["MaMean"].iloc[_ - openHour],
                        data["MaStd"].iloc[_ - openHour],
                    )
                )
                Customer.get_total_price.female.append(
                    Parameters(
                        data["FeMean"].iloc[_ - openHour],
                        data["FeStd"].iloc[_ - openHour],
                    )
                )
            return Customer.get_total_price(time, gender)

    def lifetime(self):
        if self.env.time.day == 1:
            self.env.log("beginning of shopping")
        self.env.total_total += 1
        if self.gender == Gender.Male:
            self.env.total_men += 1
        else:
            self.env.total_women += 1
        yield self.env.timeout(self.shoppingDuration)
        op = min(
            (p for p in self.env.cashdesks if p.isOpen), key=lambda p: len(p.queue)
        )  # get cashier with minimal length of queue
        if len(op.queue) > tolerablequeue:
            self.env.warningLog("leaving customer without paying")
            self.env.lostIncome += self.get_total_price(self.env.time, self.gender)
        else:
            try:
                with op.request() as req:
                    start = self.env.now
                    self.env.log("beginning of waiting")
                    op.queue.append(self)
                    yield req
                    # getting cashed
                    self.env.log("paying")
                    yield self.env.timeout(
                        random.triangular(1 * tick, 3 * tick, 10 * tick)
                    )
                    op.queue.remove(self)
                    op.pay(
                        self.gender, self.get_total_price(self.env.time, self.gender)
                    )
                    self.env.log(f"wait time= {self.env.now - start}")
                    self.env.log("end of shopping")
            except:
                pass
        self.env.total_total -= 1
        if self.gender == Gender.Male:
            self.env.total_men -= 1
        else:
            self.env.total_women -= 1


class CustomerFactory(Entity):
    """
    generating customers in infinite loop
    poisson distribution separately fro men and women, is used for generating customers
    """

    def __init__(self, env):
        super().__init__(env)
        self.env.process(self.lifetime())
        self.newCashierTime = 0

    @staticmethod
    def _get_men(time: Time):
        """
        get amount of arrived men for current minute.
        :param time: object represent time
        :return: number
        """
        return random.poisson(
            (MaMinimal * data["MaDiff"].iloc[time.hour - openHour]) / (60 / tick), 1
        )

    @staticmethod
    def _get_women(time: Time):
        """
        get amount of arrived women for current minute.
        :param time: object represent time
        :return: number
        """
        return random.poisson(
            (FeMinimal * data["FeDiff"].iloc[time.hour - openHour]) / (60 / tick), 1
        )

    def lifetime(self):
        while True:
            # generating new customers
            if not (self.env.time.hour == closeHour):
                [
                    Customer(
                        self.env,
                        Gender.Male,
                        random.triangular(5 * tick, 15 * tick, 25 * tick),
                    )
                    for _ in range(0, self._get_men(self.env.time)[0])
                ]
                [
                    Customer(
                        self.env,
                        Gender.Female,
                        random.triangular(10 * tick, 20 * tick, 30 * tick),
                    )
                    for _ in range(0, self._get_women(self.env.time)[0])
                ]
            try:
                self.env.time.update()
            except ValueError as e:  # people are still in the shop, after closing hour
                self.env.errorLog(e.__str__())
                self.env.time.hour = (
                    self.env.time.hour - 1
                )  # need to rewind time by 1 hour, becaouse we can't get total price in close hour (index out of list)
                for cash in self.env.cashdesks:
                    for p in cash.queue:
                        self.env.lostIncome += Customer.get_total_price(
                            self.env.time, p.gender
                        )
                self.env.time.hour = self.env.time.hour + 1
                self.env.collector.collect()
                self.env.total_total = 0
                self.env.time.update()
            yield self.env.timeout(tick)
            if len(self.env.cashdesks) > 1:
                # checking maximal queuee for opening another checkout
                if (
                    self.env.now - self.newCashierTime > newMinTime
                    and max((len(p.queue) for p in self.env.cashdesks if p.isOpen))
                    > max_length
                ):
                    for x in range(len(self.env.cashdesks)):
                        if not self.env.cashdesks[x].isOpen:
                            self.env.cashdesks[x].open(self.env.now)
                            self.newCashierTime = self.env.now
                            break
                # checking minimal queuee for closing checkout
                elif (
                    len([_ for _ in self.env.cashdesks if _.isOpen]) > 1
                    and min((len(p.queue) for p in self.env.cashdesks if p.isOpen))
                    < min_length
                ):
                    for x in range(len(self.env.cashdesks)):
                        if (
                            self.env.cashdesks[x].isOpen
                            and self.env.now - self.env.cashdesks[x].timeOfOpen
                            > minTime
                            and len(self.env.cashdesks[x].queue) < min_length
                        ):
                            self.env.cashdesks[x].close()
                            break


if __name__ == "__main__":
    # example of the simulation
    env = Shop(cashiers)
    env.log_off()
    s = ShopStatistic(env, sampling)
    CustomerFactory(env)
    env.run(until=simTime)
    # plotting graphs for variables by days
    for day in range(env.time.day + 1):
        # plotting graph of customers in the store
        plt.plot(s.customer[day], label="men + women")
        plt.plot(s.men[day], label="men")
        plt.plot(s.women[day], label="women")
        plt.legend()
        plt.title(f"day{day + 1}: people in the store")
        plt.show()
        # graph of customers waiting in the queuee
        plt.plot(s.byCashDesk[day], label="by cash desk")
        plt.plot(s.customer[day], label="customers in the store")
        plt.legend()
        plt.title(f"day{day + 1}: people in the queue")
        plt.show()
        # income from men,women and total
        plt.plot(s.income_total[day], label="total income")
        plt.plot(s.income_men[day], label="men")
        plt.plot(s.income_women[day], label="women")
        plt.legend()
        plt.title(f"day{day + 1}: total income")
        plt.show()
        # income of individual cashdesks
        for cash in range(cashiers):
            plt.plot(s.income_cashiers[day][cash])
            plt.title(f"day{day + 1}: income of cashier:{cash + 1}")
            plt.show()
            # length of the queuee
            plt.plot(s.queuee_cashiers[day][cash])
            plt.title(f"day{day + 1}: length of queuee cashier: {cash + 1}")
            plt.show()
        # opened cashiers
        plt.plot(s.openedCashiers[day])
        plt.title(f"day{day + 1}: number of opened cashiers")
        plt.show()
        # lost money
        plt.plot(s.lostMoney[day])
        plt.title(f"day{day + 1}: amount of lost money")
        plt.show()
    print(f"total income: {sum([max([i for i in x]) for x in s.income_total])}")
