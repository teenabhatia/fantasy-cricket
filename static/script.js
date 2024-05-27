function getScores() {
    fetch('/get_scores')
        .then(response => response.json())
        .then(data => {
            const scoresDiv = document.getElementById('scores');
            const friendPointsDiv = document.getElementById('friend-points');
            scoresDiv.innerHTML = '';
            friendPointsDiv.innerHTML = '';

            const playerScores = data.data;
            const friendPoints = data.friend_points;

            const playerScoresTable = document.createElement('table');
            playerScoresTable.border = '1';
            playerScoresTable.innerHTML = '<tr><th>Player Name</th><th>Runs</th><th>Wickets</th><th>Points</th><th>Friend Name</th></tr>';
            playerScores.forEach(player => {
                const row = playerScoresTable.insertRow();
                row.insertCell(0).textContent = player.player_name;
                row.insertCell(1).textContent = player.runs;
                row.insertCell(2).textContent = player.wickets;
                row.insertCell(3).textContent = player.points;
                row.insertCell(4).textContent = player.friend_name;
            });
            scoresDiv.appendChild(playerScoresTable);

            const friendPointsTable = document.createElement('table');
            friendPointsTable.border = '1';
            friendPointsTable.innerHTML = '<tr><th>Friend Name</th><th>Points</th></tr>';
            friendPoints.forEach(friend => {
                const row = friendPointsTable.insertRow();
                row.insertCell(0).textContent = friend.friend_name;
                row.insertCell(1).textContent = friend.points;
            });
            friendPointsDiv.appendChild(friendPointsTable);
        });
}
