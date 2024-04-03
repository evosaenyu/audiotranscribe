import streamlit as st
from streamlit_elements import elements, mui, html, sync

def slideshow_swipeable(images):
    # Generate a session state key based on images.
    key = f"slideshow_swipeable_{str(images).encode().hex()}"

    # Initialize the default slideshow index.
    if key not in st.session_state:
        st.session_state[key] = 0

    # Get the current slideshow index.
    index = st.session_state[key]

    # Create a new elements frame.
    with elements(f"frame_{key}"):

        # Use mui.Stack to vertically display the slideshow and the pagination centered.
        # https://mui.com/material-ui/react-stack/#usage
        with mui.Stack(spacing=2, alignItems="center"):

            # Create a swipeable view that updates st.session_state[key] thanks to sync().
            # It also sets the index so that changing the pagination (see below) will also
            # update the swipeable view.
            # https://mui.com/material-ui/react-tabs/#full-width
            # https://react-swipeable-views.com/demos/demos/
            with mui.SwipeableViews(index=index, resistance=True, onChangeIndex=sync(key)):
                for image in images:
                    html.img(src=image, css={"width": "100%"})

            # Create a handler for mui.Pagination.
            # https://mui.com/material-ui/react-pagination/#controlled-pagination
            def handle_change(event, value):
                # Pagination starts at 1, but our index starts at 0, explaining the '-1'.
                st.session_state[key] = value-1

            # Display the pagination.
            # As the index value can also be updated by the swipeable view, we explicitely
            # set the page value to index+1 (page value starts at 1).
            # https://mui.com/material-ui/react-pagination/#controlled-pagination
            mui.Pagination(page=index+1, count=len(images), color="primary", onChange=handle_change)
