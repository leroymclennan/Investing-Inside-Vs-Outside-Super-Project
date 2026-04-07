import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# This counter determines how new windows are open: 0 -> Top left, 1 -> Top right, 2 -> Bottom left, 3 -> Bottom right
plot_window_counter = 0

############################
# Function to run simulation
############################
def run_simulation():
    """
    Runs a simulation of two investment strategies: one where all disposable income is invested outside super, and another where all disposable income is invested in super.

    The simulation takes into account the user's current age, time horizon, current ETF investment, current super balance, super fees, annual income, investable income, expected return, wage growth, and marginal tax rate.

    The simulation outputs a graph comparing the two investment strategies, with the final balances annotated on the graph.
    """
    try:
        # Get user inputs from GUI
        current_age = int(age_entry.get())
        time_horizon = int(horizon_entry.get())
        current_etf = float(etf_entry.get())
        current_super = float(super_entry.get())
        super_fee_percent = float(fee_percent_entry.get()) / 100
        super_fee_fixed = float(fee_fixed_entry.get())
        current_income = float(income_entry.get())
        investable_income = float(investable_income_entry.get())
        expected_return = float(return_entry.get()) / 100
        wage_growth = float(wage_growth_entry.get()) / 100
        mandatory_super_rate = 0.12  # 12% compulsory super

        # Take the list selection from the GUI and turn it into the marginal tax rate
        tax_option = tax_var.get()
        marginal_tax_rates = {'19%':0.19, '30%':0.3, '37%':0.37, '45%':0.45}
        marginal_tax_rate = marginal_tax_rates.get(tax_option, 0.30)

        # Prepare dataframe
        ages = np.arange(current_age, current_age + time_horizon + 1)
        balances = pd.DataFrame(index=ages, columns=['ETF_strategy', 'Super_strategy'])

        # Calculate what the ETF values are at the end of each year
        etf_balance_etf_strategy = current_etf
        etf_balance_super_strategy = current_etf

        # Calculate what the super values are at the end of each year
        super_balance_etf_strategy = current_super
        super_balance_super_strategy = current_super

        # Tax concessions for the super strategy kick in 1 financial year later, hence first year they are 0
        tax_concession_amount_prior_FY = 0

        # Dividend tax rates - Assume dividends are 1% of AUM per year, super is taxed at 15%, ETF is taxed at marginal rate
        super_dividend_tax_amount = 0.01*0.15
        etf_dividend_tax_amount = 0.01*marginal_tax_rate

        # ETF Fees
        etf_fee = 0.005

        # Initialize annual income and disposable income
        annual_income = current_income
        annual_investable_income = investable_income

        for age in ages:
            # Strategy 1: Disposable income invested in ETFs outside super
            # ETF value = previous ETF value times by growth rate, plus annual contributions
            etf_balance_etf_strategy = etf_balance_etf_strategy * (1 + expected_return - etf_dividend_tax_amount - etf_fee) + annual_investable_income
            # Super value = previous super value times by growth rate, minus super fees, plus mandatory contributions
            super_balance_etf_strategy = super_balance_etf_strategy * (1 + expected_return - super_dividend_tax_amount) \
                                        - (super_balance_etf_strategy * super_fee_percent + super_fee_fixed) \
                                        + annual_income * mandatory_super_rate
            # Strategy total = super + ETF values
            balances.loc[age, 'ETF_strategy'] = etf_balance_etf_strategy + super_balance_etf_strategy

            # Strategy 2: All disposable income being invested in super
            # ETF value = previous ETF value times by growth rate, but with no annual contributions given the strategy
            etf_balance_super_strategy = etf_balance_super_strategy * (1 + expected_return - etf_dividend_tax_amount - etf_fee)
            # Super balance = previous super value times by growth rate (minus tax on dividends), minus super fees, plus mandatory contributions, plus the tax refund on the voluntary super contributions (taxed at 15% as opposed to marginal tax rate)
            super_balance_super_strategy = super_balance_super_strategy * (1 + expected_return-super_dividend_tax_amount) \
                                           - (super_balance_super_strategy * super_fee_percent + super_fee_fixed) \
                                           + annual_income * mandatory_super_rate \
                                           + annual_investable_income + tax_concession_amount_prior_FY
            # Strategy total = super + ETF values
            balances.loc[age, 'Super_strategy'] = super_balance_super_strategy + etf_balance_super_strategy

            # Calculate the tax concession from this year that will be used for next year
            tax_concession_amount_prior_FY = (marginal_tax_rate-0.15)*annual_investable_income

            # Apply annual wage growth
            annual_income *= (1 + wage_growth)
            annual_investable_income *= (1 + wage_growth)

        # Plot
        fig = plt.figure(figsize=(10, 5))
        position_plot_window(fig)
        plt.plot(balances.index, balances['ETF_strategy'], label='ETF + Mandatory Super', linewidth=2)
        plt.plot(balances.index, balances['Super_strategy'], label='Extra Super Contributions', linewidth=2)

        # Annotate final balances with breakdown of balances
        plt.text(current_age+1/3*time_horizon, balances['Super_strategy'].iloc[-1], f"Investing OUTSIDE Super Strategy\nTotal Balance: ${balances['ETF_strategy'].iloc[-1]:,.0f}\nSuper Balance: ${np.round(super_balance_etf_strategy,0):,.0f}", ha='left', va='top')
        plt.text(current_age+1/3*time_horizon, 5/6*balances['Super_strategy'].iloc[-1], f"Investing INSIDE Super Strategy\nTotal Balance: ${balances['Super_strategy'].iloc[-1]:,.0f}\nSuper Balance: ${np.round(super_balance_super_strategy,0):,.0f}", ha='left', va='top')

        plt.xlabel('Age')
        plt.ylabel('Portfolio Balance ($)')
        plt.title('Investment Strategy Comparison')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    except ValueError:
        messagebox.showerror("Input Error", "Please make sure all fields are filled correctly with numeric values.")

########################
# Graph window positions
########################
def position_plot_window(fig):
    """
    Positions the plot window in a different position on the screen for each call.
    
    The positions are defined as follows:

    - Top-left: (horizontal_margin, vertical_margin)
    - Top-right: (horizontal_margin + window_width + horizontal_gap, vertical_margin)
    - Bottom-left: (horizontal_margin, vertical_margin + window_height + vertical_gap)
    - Bottom-right: (horizontal_margin + window_width + horizontal_gap, vertical_margin + window_height + vertical_gap)

    The window size is slightly smaller than half the screen's dimensions to prevent overlap.
    
    :param fig: The figure to be positioned
    :type fig: matplotlib.figure.Figure
    """ 
    global plot_window_counter

    manager = plt.get_current_fig_manager()

    # Get screen dimensions so plots  can be scaled to fit
    screen_width = root.winfo_screenwidth()-10 # Measures appears off on my own screen, these adjustments centres it on my screen, but may not centre it on yours
    screen_height = root.winfo_screenheight()-80

    # Add margins and spacing between the plots
    horizontal_margin = 10
    vertical_margin = 10
    horizontal_gap = 10
    vertical_gap = 40

    # Window size (slightly smaller than half screen so it doesn't overlap)
    window_width = (screen_width - horizontal_margin * 2 - horizontal_gap) // 2
    window_height = (screen_height - vertical_margin * 2 - vertical_gap) // 2

    # Define positions
    positions = [
        (horizontal_margin, vertical_margin),  # Top-left
        (horizontal_margin + window_width + horizontal_gap, vertical_margin),  # Top-right
        (horizontal_margin, vertical_margin + window_height + vertical_gap),  # Bottom-left
        (horizontal_margin + window_width + horizontal_gap, vertical_margin + window_height + vertical_gap)  # Bottom-right
    ]

    x, y = positions[plot_window_counter % 4]

    try:
        manager.window.wm_geometry(f"{window_width}x{window_height}+{x}+{y}")
    except:
        pass

    plot_window_counter += 1

########################
# Graph closer function
########################

def close_all_graphs():
    """
    Close all graphs that have been opened by the program, whilst leaving GUI open for further graph generation
    """
    plt.close('all')

###########
# GUI Setup
###########

root = tk.Tk()
root.title("Investment Strategy Simulator")

entries = []
entry_width = 20

# Labels and entries of the GUI
labels = ["Current Age (years)", 
          "Time Horizon (years)", 
          "Current ETF Investment ($ total)", 
          "Current Super Balance ($ total)",
          "Super Fee % (per year)", 
          "Super Fee Fixed ($ per year)", 
          "Annual Income ($ per year)", 
          "Investable Income ($ per year)", 
          "Expected Stock Return (% per year)", 
          "Annual Wage Growth (% per year)"]


# Create the GUI elements going through labels list entry by entry
for i, label in enumerate(labels):
    tk.Label(root, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=2)
    entry = tk.Entry(root, width=entry_width)
    entry.grid(row=i, column=1, padx=5, pady=2)
    entries.append(entry)

# Variable names assigned with each entry
(age_entry, horizon_entry, etf_entry, super_entry, fee_percent_entry, fee_fixed_entry, 
 income_entry, investable_income_entry, return_entry, wage_growth_entry) = entries

# Marginal Tax Rate selection - dropdown read only list for selecting the various marginal tax rate options
tk.Label(root, text="Marginal Tax Rate").grid(row=len(labels), column=0, sticky="w", padx=5, pady=2)
tax_var = tk.StringVar()
tax_dropdown = ttk.Combobox(
    root,
    textvariable=tax_var,
    values=["19%", "30%", "37%", "45%"],
    state="readonly",
    width = int(entry_width*0.85)
)
tax_dropdown.grid(row=len(labels), column=1, padx=5, pady=2)
tax_dropdown.set("30%")  # default selection for most people

# Close All Graphs button (left)
close_btn = tk.Button(
    root,
    text="Close All Graphs",
    command=close_all_graphs,
    bg="lightcoral",
    width=18
)
close_btn.grid(row=len(labels)+2, column=0, padx=10, pady=15, sticky="w")

# Run Simulation button (right)
run_btn = tk.Button(
    root,
    text="Run Simulation",
    command=run_simulation,
    bg="lightgreen",
    width=18
)
run_btn.grid(row=len(labels)+2, column=1, padx=10, pady=15, sticky="e")

root.mainloop()