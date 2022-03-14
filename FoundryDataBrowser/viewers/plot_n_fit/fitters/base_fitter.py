"""
Created on Mar 9, 2022

@author: Benedikt Ursprung
"""
from ScopeFoundry.logged_quantity import LQCollection
import numpy as np
from .qwidget import FitterQWidget
from FoundryDataBrowser.viewers.plot_n_fit.helper_functions import table2html


class BaseFitter:
    """    
        *fit_params* list of parameters to be optimized and associated values: 
                     [
                     ['ParamName0', (initial0, lower_bound0, upper_bound0, vary0)] 
                     ['ParamName1', (initial1, lower_bound1, upper_bound1)]
                     ...'
                     ] 
                        
        *name*       any string 
        
        Implement `fit_xy(x,y)`
        
        <LeastSquaresBaseFitter> might be easier to use.
        
        other useful function to override:
            process_results
            add_derived_result_quantities
    """

    fit_params = []
    name = "xy_base_fitter"

    def __init__(self):

        self.fit_results = LQCollection()
        self.derived_results = LQCollection()
        self.settings = LQCollection()
        self.initials = LQCollection()
        self.vary = LQCollection()
        self.bounds = LQCollection()

        for name, init in self.fit_params:
            self.fit_results.New(name, initial=0.0)
            if init is None:
                continue
            if len(init) in (3, 4):
                if len(init) == 4:
                    (val, lower, upper, vary) = init
                    self.vary.New(name, bool, initial=vary)
                else:
                    (val, lower, upper) = init
                    vary = True

                self.bounds.New(name + "_lower", initial=lower)
                self.bounds.New(name + "_upper", initial=upper)
                self.initials.New(name, initial=val, si=True)

        self.use_bounds = self.settings.New("use_bounds", bool, initial=False)

        self.add_derived_result_quantities()
        self.add_settings_quantities()

        self.ui = FitterQWidget()
        self.ui.add_collection_widget(self.settings, "settings")
        self.ui.add_collection_widget(self.initials, "initials")
        self.ui.add_collection_widget(self.vary, "vary")
        self.ui.add_enabable_collection_widget(self.bounds, "bounds", self.use_bounds)

        self.ui.add_button("initials from results", self.set_initials_from_results)

        self.result_message = self.name + ": result_message message not set yet"

        self.highlight_x_vals = []  # just a container for x_values that can be used

    def fit_xy(self, x: np.array, y: np.array) -> np.array:
        """ 
        has to return an array with the fit of len(y)
        recommended properties/functions to use:
            
            self.initials_array
            self.bounds_array
            
            self.update_fit_results(fit_results, additional_msg) 
                [recommended if the number of fit_params is fixed]
                otherwise pass a string to self.set_result_message(message)
                
            return fit #this 
        """
        raise NotImplementedError()

    def update_fit_results(self, fit_results, additional_msg=""):
        """
        helper function, which updates the results
        quantitiy collection and sets the result_message.
        the order of *results_array* is the 
        same as the order the parameters were defined.        
        Note: this function calls self.process_results
        before updating the results table.
                    
        alternatively pass a string to set_result_message(message)
        """
        processed_fit_results = self.process_results(fit_results)
        for val, lq in zip(processed_fit_results, self.fit_results.as_list()):
            lq.update_value(val)

        res_table = self.get_result_table(decimals=3)
        header = ["param", "value", "unit"]
        html_table = table2html(res_table, header=header)
        if additional_msg != 0:
            msg = html_table + f"<p margin-top=5px>{additional_msg}</p>"
            self.set_result_message(msg)
        else:
            self.set_result_message(html_table)

    def add_derived_result_quantities(self):
        """add results other than fit_params eg: 
        self.derived_results.New('resX', ...), 
        use `process_results` to update this quantities!
        """
        pass

    def process_results(self, fit_results):
        """
        calculate and set derived_results here, this function will be called
        in update_fit_results. The fit_results quantities are set according 
        to the output of this function. 
        Hence this function has to return the (processed) fit results in the 
        correct order, that the order they were defined in fit_params.       
        """
        processed_fit_results = fit_results
        return processed_fit_results

    def add_settings_quantities(self):
        """
        add results other than fit_params e.g: self.results.New('resX', ...), 
        set them in process_results
        """
        pass

    @property
    def bounds_array(self):
        """returns least_square style bounds array"""
        if self.settings["use_bounds"]:
            f = filter(lambda lq: lq.name.endswith("lower"), self.bounds.as_list())
            lower_bounds = [lq.val for lq in f]
            f = filter(lambda lq: lq.name.endswith("upper"), self.bounds.as_list())
            upper_bounds = [lq.val for lq in f]
        else:
            N_bound_pairs = len(self.initials.as_list())
            lower_bounds = [-np.inf] * N_bound_pairs
            upper_bounds = [np.inf] * N_bound_pairs
        return np.array([lower_bounds, upper_bounds])

    @property
    def derived_results_array(self):
        return np.array([lq.val for lq in self.derived_results.as_list()])

    @property
    def fit_results_array(self):
        return np.array([lq.val for lq in self.fit_results.as_list()])

    @property
    def initials_array(self):
        return np.array([lq.val for lq in self.initials.as_list()])

    @property
    def initials_dict(self):
        d = {}
        for k, v in self.initials.as_value_dict():
            if self.vary[k]:
                d[k] = v
        return d

    @property
    def constants_array(self):
        return np.array(
            [lq.val for name, lq in self.initials.as_dict() if self.vary[name]]
        )

    def hyperspec_descriptions(self):
        """overwrite these if the results of fit_hyperspec is not
        fully described by fit_params!"""
        return [self.name + "_" + lq.name for lq in self.fit_results.as_list()]

    def fit_hyperspec(self, t, _hyperspec, axis=-1):
        """
        intended for multidimensional arrays.
        Convention: this function should fit along *axis* and should 
                    return the params along the 0th axis! 
        """
        raise NotImplementedError(self.name + "_fit_hyperspec() not implemented")

    def get_result_table(self, decimals=3, include=None):
        res_table = []
        for lq in list(self.fit_results.as_list()) + list(
            self.derived_results.as_list()
        ):
            if include == None or lq.name in include:
                q = lq.name
                val = "{:4.{prec}f}".format(lq.val, prec=decimals)
                if lq.unit is not None:
                    unit = "{}".format(lq.unit)
                else:
                    unit = ""
                res_table.append([q, val, unit])
        return res_table

    def set_result_message(self, message):
        self.result_message = message
        self.ui.set_result_message(message)

    def set_initials_from_results(self):
        for k in self.initials.as_dict().keys():
            self.initials[k] = self.fit_results[k]

    @property
    def state_info(self):
        return self.name + self.state_description()

    def state_description(self):
        return ""
