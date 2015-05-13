/** @jsx React.DOM */

var Greeting = React.createClass({
    getInitialState: function () {
        return {greeting_text: 'UI is not implemented yet!'};
    },

    render: function () {
        return (
            <div>
                <p><i>{this.state.greeting_text}</i></p>
            </div>
        )
    }
});

React.render(
    <Greeting/>,
    document.getElementById('main')
);
