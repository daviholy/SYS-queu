from .view_controller import Simulation


if __name__ == "__main__":
    simulation = Simulation([1,2, 4, 8, 16, 32,64])
    simulation.run()