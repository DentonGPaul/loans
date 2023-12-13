import pandas as pd
import datetime as dtm
from bokeh.plotting import figure, show, curdoc
from bokeh.models import ColumnDataSource, DateRangeSlider, Slider, TextInput, Button, Div, HoverTool
from bokeh.layouts import column, row
from bokeh.client import push_session
import pytz
#
# Your existing functions with minor adjustments
def get_min_payment(years, R, P):
    r = (R/100)/12
    n = years * 12
    M = (P*r*((1+r)**n))/(((1+r)**n)-1)
    return M

def simulate(years, R, P, start_date, extra_payments = 0):
    Pn = P
    r = (R/100)/12
    _n = years * 12
    M = get_min_payment(years, R, P)

    d = {}
    for n in range(_n):
        paid_interest = Pn*r
        paid_principal = (M - paid_interest) + extra_payments

        if paid_principal > Pn:
            paid_principal = Pn

        payment = paid_principal + paid_interest

        Pn = Pn - paid_principal
        d[n] = {'Pn': Pn, 'Principal Payment': paid_principal, 'Interest Payment': paid_interest, 'Payment': payment}

        if Pn <= 0 :
            break

    df = pd.DataFrame.from_dict(d, orient='index')
    y, m = int(df.shape[0]/12), df.shape[0]%12
    total_paid = df.Payment.sum()

    df.index = pd.date_range(start=start_date, periods=df.shape[0], freq='M')

    return df, y, m, total_paid, M + extra_payments

# Create a ColumnDataSource
source = ColumnDataSource(data={'x': [], 'y1': [], 'y2': [], 'y3': []})

# Create a plot
plot = figure(title='Loan Payment Simulation', x_axis_type='datetime', plot_height=400, plot_width=700)
plot.line('x', 'y1', source=source, legend_label='Principal Payment', color='blue')
plot.line('x', 'y2', source=source, legend_label='Interest Payment', color='red')
# Create a HoverTool object
hover = HoverTool(
    tooltips=[
        ("Date", "@x{%F}"),  # %F is the format for full ISO date
        ("Principal", "@y1{$0,0.00}"),  # Formatting as currency
        ("Interest", "@y2{$0,0.00}")  # Formatting as currency
    ],
    formatters={
        '@x': 'datetime',  # Use 'datetime' formatter for '@x' field
    },
    mode='vline'
)

# Add the HoverTool to the plot
plot.add_tools(hover)

# Create a new plot for Pn values
pn_plot = figure(title='Remaining Loan Balance Over Time', x_axis_type='datetime', plot_height=400, plot_width=700)
pn_plot.line('x', 'y3', source=source, legend_label='Loan Balance', color='blue')
hover_pn = HoverTool(
    tooltips=[
        ("Date", "@x{%F}"),  # %F is the format for full ISO date
        ("Loan Balance", "@y3{$0,0.00}"),  # Formatting as currency
    ],
    formatters={
        '@x': 'datetime',  # Use 'datetime' formatter for '@x' field
    },
    mode='vline'
)
pn_plot.add_tools(hover_pn)

# Widgets
years_input = Slider(title="Loan Duration (Years)", value=30, start=1, end=40, step=1)
rate_input = Slider(title="Annual Interest Rate (%)", value=5.0, start=2, end=10.0, step=0.01)
principal_input = Slider(title="Loan Amount", value=330000, start=5000, end=500000, step=1000)
today = dtm.datetime.now(tz=pytz.timezone('America/New_York')).date().strftime('%Y-%m-%d')
start_date_input = TextInput(title="Start Date (YYYY-MM-DD)", value=today)
extra_payment_input = Slider(title="Extra Monthly Payment", value=0, start=0, end=1000, step=25)
update_button = Button(label="Update", button_type="success")
loan_duration_div = Div(text="Loan Duration: ", width=300, height=15)
total_paid_div = Div(text="Total Paid: ", width=300, height=15)
monthly_fixed_payment = Div(text="Monthly Payment: ", width=300, height=15)
end_date = Div(text="End Date: ", width=300, height=15)

# Update function
def update():
    # Get values from widgets
    years = years_input.value
    R = rate_input.value
    P = principal_input.value
    start_date = dtm.datetime.strptime(start_date_input.value, '%Y-%m-%d').date()
    extra_payments = extra_payment_input.value

    # Run simulation
    df, y, m, total_paid, M = simulate(years, R, P, start_date, extra_payments)

    # Update the data source
    source.data = {
        'x': df.index,
        'y1': df['Principal Payment'].to_list(),
        'y2': df['Interest Payment'].to_list(),
        'y3': df['Pn'].to_list()
        }
    
    loan_duration_div.text = f"Loan Duration: {y} years and {m} months"
    total_paid_div.text = f"Total Paid: ${total_paid:,.2f}"
    monthly_fixed_payment.text = f"Monthly Payment: ${M:,.2f}"
    end_date.text = f"End Date: {df.index[-1].date()}"

update_button.on_click(update)

# Layout
info_layout = column(monthly_fixed_payment, loan_duration_div, total_paid_div, end_date)
inputs = column(years_input, rate_input, principal_input, start_date_input, extra_payment_input, update_button, info_layout)
layout = row(inputs, column(plot, pn_plot))

# Add the layout to the current document
curdoc().add_root(layout)
session = push_session(curdoc())
session.show()