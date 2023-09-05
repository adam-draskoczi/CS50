# Bonbons
#### Video Demo:    https://youtu.be/dqhidrnzuU0

NOTE: This project is being continously updated and improved as I keep getting to know new concepts and tools of programming.

#### Description:

Welcome to Bonbons!

I created this web app as my final project for CS50x. The idea is coming from my actual job in the field of production and process engineering. This web app imitates the type of product and volume sizing that I have been manufacturing.

Let's imagine a factory that manufactures bonbons. This happens in 3+1 steps: Filling, Coating, Topping + Quality inspection.
Bonbons are created in batches. A batch is made up of 5 boxes. Each box contains 10 bonbons, therefore each batch consists of 50 bonbons. Each of the 10 bonbons in a box is created on a separate line but with the same parameters within the box. Boxes within the same batch can have different parameters.

These production parameters are: 
The type of chocolate used: Milk, Dark or White. 
The temperature of the process in Celsius degrees (°C).

After a batch is fully processed, Quality inspectors track every defect on the individual bonbons with unique defect codes.

#### bonbons.db

This file contains the SQL database my program uses.

The `users` table stores user-related data, including a unique ID, username, hashed login password, name, work area, title, and registration timestamp.

The `batches` table contains information about batches. Each batch is assigned a unique ID and has associated attributes such as a name, an optional comment, the ID of the user who created the batch (referenced by the ID in the `users` table), as well as timestamps for all processes and quality steps. These timestamps remain NULL until the corresponding processes are completed.

The `bonbons` table maintains data for individual bonbons. Each bonbon possesses a unique ID and is identified by the batch it belongs to, the box it is stored in, and the line it was created on. The batch is referenced by its ID from the `batches` table.

The `processes` table stores information about the various processes carried out on each box within a batch. The box is referenced by its ID from the `batches` table. For each process, the table records the process type, temperature, type of chocolate used, optional comments, the user who performed the process (referenced by their ID from the `users` table), and the timestamp of the process.

The `inspection` table captures data pertaining to defects found on individual bonbons. Each defect is linked to a specific bonbon using its ID from the `bonbons` table. The table also includes information about the user who logged the defect (referenced by their ID from the `users` table) and the timestamp of the inspection.

You can also view the utilised `CREATE TABLE` commands in `sql.txt`.

#### app.py

This file encompasses the view functions of the application.

The header section incorporates essential components from libraries as well as several lists of tuples containing commonly required data. Subsequently, these elements are passed as inputs to the corresponding template renderings.

A context_processor decorator is employed to supply data that is typically necessary for all sites when a user is logged in. This data includes:

* The record of the currently logged-in user fetched from the `users` table.
* A dynamic query that retrieves all pending batches awaiting processing in the user's work area.

The root route ("/") guides the user either to the index page (if not logged in) or to the homepage (if logged in).

The `/home` route facilitates the retrieval of the homepage when the user is logged in.

In response to a GET request, the `register()` function within the `/register` route returns the registration page, as defined by an external function called `signup()` (located in function.py). Upon submitting the registration form, the function extracts the relevant data, converts the password into a hash, records the registration time (based on the backend server), and stores these details as a new row in the `users` table. Finally, the user is redirected to `/login` and presented with a flash message confirming the successful registration.

The `login()` function within the `/login` route performs a redirection to the `login.html` page (or to the homepage if the user is already logged in). Upon receiving a POST request, the function executes a query to locate any rows in the `users` table with a matching username. If no matches are found, the user is redirected back to the login page along with a warning flash message.

If the provided username appears to be valid, the function compares the corresponding password with the hash stored in the same row within the `users` table. In the case of an incorrect password, the user is once again redirected and alerted.

If both the username and password are deemed valid and matching, the user's ID is stored in the session, while the user is being redirected to the homepage.

The `/logout` route clears the session, redirects the page to the index site and confirms successful logout via a flash message.

All other routes and view functions within are calling external functions defined in `features.py`.

#### features.py

The `/batch` route in `app.py` calls `batch()`, which in case of a GET request returns `batch_new()`. The function queries the already existing batch names from the table `batches` and passes them into `batch.html`, where the form is submitted to send a POST request to the same route. This calls `batch_saved()` which saves the batches name, comment, creator user's ID and creation timestamp in the `batches` table. The function also creates 50 new rows in `bonbons` with unique IDs, representing the 50 new bonbons in the newly created batch. The function then redirects the user to the homepage, with a flash message confirming the successful creation of a new batch.

The `/process` route in `app.py` calls the `process()` function. A GET request calls the `process_new()` function, which queries the comments from the selected batch's row in `batches` table and passes it into `process.html`, along with the name of the batch and the process (area) of the user logged in.
The `process_saved()` function (called upon POST request) saves the process data in `processes` for each box within the batch and updates the row of batch in `batches` table with the timestamp of process done. The function then redirects to view the details of the batch, passing the batchname into the routing. This route calls the `batch_details()` function, which queries the process data from `processes` table for the batch in question and saves them in list of list of dicts for each process type. The function then renders `batch-details.html`, passing the process data along with workers and areas data.

Upon a GET request, the `inspection()` function in the `/inspection` route calls the `inspection_new()` function. The function queries the data of bonbons in the selected batch from `bonbons` table and creates a dict, where the key of each element is the position of the bonbon (box and line), whereas the values are the bonbons' IDs. The function also checks if a batch has been already inspected. All this information, along with the defects' list is being passed into the rendered `inspection.html` page.
Submitting the inspection sends a POST request, which in return, calls the `inspeciton_saved()` function. This updates the timestamp of latest quality inspection in the batch's row in the `batches` table. The inspection data is deleted according to the chosen action. Thereafter the function saves the newly recorded defects into the `inspections` table, creating a new row for each bonbon and defect, making sure that repeating defects are not double-logged. The function then redirects to the `/view_inspection` route, calling the `inspection_view()` function.

This function selects the inspection data for the selected batch's bonbons based on their ID and saves them in a dict, using the bonbons's positions as keys and the (list of) defects as values. This is then passed into the `inspection-saved.html`, along with the time of the latest quality inspection and the batch data.

The `overview()` function at the `/overview` route calls the `batch_overview()` function, which collects the necessary user and batch data of all existing batches, passing them into the rendered `overview.html` page.

The `/analyse` route renders the `analyse.html` template, passing the list of processes, parameters and defects along. The form, once submitted, triggers the `/analysis` route, which calls the `analysis_data()` function, which in return calls the `analysis()` function. This function routes into two ways:
* If the parameter is the line on which the bonbons ran, the function queries the number of runs (which equals the number of bonbons processed on each line) and checks the number of defected bonbons, where the line is the same in `bonbons` table.
* If the parameter is temperature or type, the functions queries all the distinct values of that parameter from previous processes of the selected type, finds all the boxes ran with each value and takes the number of all and defected bonbons.
It then collects all data per each value (line, temperature or type of chocolate) in a list of dicts, formatted as needed. Finally all these data is sent to rendering of `analysis.html`.

#### helpers.py

This file contains an implementation of the `dict_factory()` function, which is used for each query to get the SQL tables' rows as dicts.

#### function.py

This file contains the `login_required(f)` function, which is called to wrap each view function that needs the user to be logged in.

The file also contains`signup()`. This function queries the existing users' usernames and passes to the rendering of the registration site.

#### aid.txt

Contains the data for mock user profiles.

### Templates

`layout.html` is the base template for all other `.html` files. It contains the Bootstrap head data as well as the top toolbar and offcanvas sidebar for logged in users. The sidebar is used to reach the majority of routes, depending on what area and role the user works in.

`index.html` is the root route's page, detailing the imaginary factory and giving option to Log In or Sign Up.

`home.html` is the landing page for authenticated users. From this on, the sidebar can be reached.

`register.html`and `login.html`, `batch.html`, `process.html`, `inspection.html` and `analyse.html` are mostly forms, collecting the necessary data and redirecting to the relevant route. Some of these utilises pre-queried lists and dicts to autofill data or check repetition with already logged data.

`batch-details.html`, `inspection-saved.html`, `overview.html` and `analysis.html` are tables, populating each row with dicts from the functions rendering these templates.
