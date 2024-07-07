import React, { useState, useEffect, useCallback } from "react";
import { Map, Marker, ZoomControl } from "pigeon-maps";
import { rgbToHex, withStyles } from "@material-ui/core/styles";
import io from "socket.io-client";

const styles = (theme) => ({
  root: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "space-around",
    overflow: "hidden",
    backgroundColor: theme.palette.background.paper,
    marginTop: "100px",
  },
  gridList: {
    width: 500,
    height: 450,
  },
  subheader: {
    width: "100%",
  },
});

const markerColors = {
  // Cop is red marker
  'cop'  : rgbToHex('#ff0000'),

  // Mafia is green marker
  'mafia': rgbToHex('#000000') 
};

const markerColors2 = {
  'cop':`rgb(255, 0, 0)`, // red
  'mafia':`rgb(149, 188, 208)`  // blue
};

// Server address and port defined as env variables
const server_address = `${process.env.REACT_APP_API_SERVICE_URL}`;

// Establish websocket connection with Flask application
const socket = io(server_address);

function GeoLocation(props) {
  // Set initial values for Latitude, Longitude, Heading, and Speed
  const [Lat, setLat] = useState("Fetching Location");
  const [Lon, setLng] = useState("Fetching Location");
  const [Hea, setHea] = useState(null);
  const [Spd, setSpd] = useState(null);

  // Define the default zoom level
  const [zoom, setZoom] = useState(18);

  // Define the default height
  const defaultHeight = 600;

  // Define the default latitude and longitude values
  const defaultLatitude = 42.33528042187331;
  const defaultLongitude = -71.09702787206938;

  // Set the default center for the map
  const [center, setCenter] = useState([defaultLatitude, defaultLongitude]);

  // Set default active cop players 
  const [playersCop, setplayersCop] = useState({});

  // Set default active cop players 
  const [playersMafia, setplayersMafia] = useState({});
  
  // Default value (in milliseconds) for updateLocation 
  // interval (1 second = 1000 ms)
  const copUpdateDuration = 3000; // 3 seconds for Cop
  const mafiaUpdateDuration = 6000; // 6 seconds for Mafia

  // Default state for marker tooltips
  const [tooltip, setTooltip] = useState({ 
    visible: false, 
    userId: null, 
    latitude: null, 
    longitude: null 
  });

  // Read cookie and return the required value
  const readCookie = (name) => {
    const cookies = document.cookie
      .split("; ")
      .find((row) => row.startsWith(`${name}=`));
    return cookies ? cookies.split("=")[1] : null;
  };

  // Report player location (and any other data)
  const reportPlayerLocation = useCallback((userId, role, latitude, longitude) => {
    const requestFields = {
      'id': userId,
      'role': role,
      'lat': latitude,
      'lon': longitude
    };

    try {
      const URI = server_address.concat("/location");
      const requestConfiguration = {
        method: "POST",
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify(requestFields)
      };

      const response = fetch(URI, requestConfiguration);

      if (response.ok) {
        console.log("Server responded!");
        try {
          const responseData = response.json();
          console.log(responseData);
        } catch (error) {
          alert("Error occurred in responseData!");
          console.error(error);
        }
      }
    } catch (error) {
      alert("Error occurred in reportPlayerLocation!");
      console.error(error);
    }
  }, []);

  const updateLocation = useCallback(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude);
          setLng(position.coords.longitude);
          setHea(position.coords.heading);
          setSpd(position.coords.speed);

          setCenter([position.coords.latitude, position.coords.longitude]);
          reportPlayerLocation(
            readCookie('userId'), 
            readCookie('role'),
            position.coords.latitude, 
            position.coords.longitude
          );
        },
        (e) => {
          console.log(e);
        }
      );
    } else {
      console.log("GeoLocation not supported by your browser!");
    }
    console.log("Updating position now...")
  }, [reportPlayerLocation]);

  // UseEffect hook to update location every 'x' seconds
  useEffect(() => {
    const role = readCookie('role');
    const interval = setInterval(updateLocation, role === 'cop' ? copUpdateDuration : mafiaUpdateDuration);
    return () => clearInterval(interval);
  }, [updateLocation]);

  // UseEffect hook to broadcast location
  useEffect(() => {
    socket.on('cop_location_update', (data) => {
      setplayersCop((prevUsers) => ({ ...prevUsers, ...data }));
    });

    socket.on('mafia_location_update', (data) => {
      setplayersMafia((prevUsers) => ({ ...prevUsers, ...data }));
    });

    socket.on('all_users', (data) => {
      setplayersCop(data);
      setplayersMafia(data);
    });

    socket.on('game_over', (data) => {
      // Display game outcome
      alert(data.result);
    });

  }, [updateLocation]);

  // UseEffect hook to broadcast location
  useEffect(() => {
    socket.on('cop_location_update', (data) => {
      setplayersCop((prevUsers) => ({ ...prevUsers, ...data }));
    });

    socket.on('mafia_location_update', (data) => {
      setplayersMafia((prevUsers) => ({ ...prevUsers, ...data }));
    });

    socket.on('all_users', (data) => {
      setplayersCop(data);
      setplayersMafia(data);
    });

    socket.on('game_over', (data) => {
      // Display game outcome
      alert(data.result);
    });

    return () => {
      socket.off('cop_location_update');
      socket.off('mafia_location_update');
      socket.off('all_users');
      socket.off('game_over');
    };
  }, []);

  const mouseHoverActiveHandler = (userId, latitude, longitude) => {
    setTooltip({ 
      visible: true, 
      userId, 
      latitude, 
      longitude 
    });
  };

  const mouseHoverInactiveHandler = () => {
    setTooltip({ 
      visible: false, 
      userId: null, 
      latitude: null, 
      longitude: null 
    });
  };

  return (
    <div style={{ backgroundColor: "white", padding: 72 }}>
      <br></br>

      <h2>
        Player {
          readCookie('userId').concat(" spawning as ").concat(readCookie('role'))
        }
      </h2>
      <h3>
        Player {
          readCookie('userId').concat("'s coordinates:")
        }
      </h3>
      <h3>
        Latitude: {Lat}
      </h3>
      <h3>
        Longitude: {Lon}
      </h3>

      <h1>Map</h1>
      <Map
        height={defaultHeight}
        center={center}
        defaultZoom={zoom}
        onBoundsChanged={({ center, zoom }) => {
          setCenter(center);
          setZoom(zoom);
        }}
      >
        {Object.keys(playersCop).map((userId) => {
          const user = playersCop[userId];
          const color = markerColors2[playersCop[userId].role];
          const latitude = Number(playersCop[userId].latitude);
          const longitude = Number(playersCop[userId].longitude);
          console.log(`Marker for user ${userId}:`, user, `Color: ${color}`);
          return (
            <Marker
              key={userId}
              width={70}
              color={color}
              anchor={[latitude, longitude]}
              onMouseOver={
                () => mouseHoverActiveHandler(
                  userId, 
                  playersCop[userId].latitude, 
                  playersCop[userId].longitude
                )
              }
              onMouseOut={mouseHoverInactiveHandler}
            />
          );
        })}
        {Object.keys(playersMafia).map((userId) => {
          const user = playersMafia[userId];
          const color = markerColors2[playersMafia[userId].role];
          const latitude = Number(playersMafia[userId].latitude);
          const longitude = Number(playersMafia[userId].longitude);
          console.log(`Marker for user ${userId}:`, user, `Color: ${color}`);
          console.log(`Latitude: ${latitude}, Longitude: ${longitude}`);
          return (
            <Marker
              key={userId}
              width={50}
              color={color}
              anchor={[latitude, longitude]}
              onMouseOver={
                () => mouseHoverActiveHandler(
                  userId, 
                  playersMafia[userId].latitude, 
                  playersMafia[userId].longitude
                )
              }
              onMouseOut={mouseHoverInactiveHandler}
            />
          );
        })}

        <ZoomControl />
      </Map>

      {tooltip.visible && (
        <div
          style={{
            position: 'absolute',
            backgroundColor: 'white',
            padding: '5px',
            border: '1px solid black',
            borderRadius: '3px',
            top: '100px',
            left: '100px',
          }}
        >
          {/* <p>User ID: {tooltip.userId}</p>
          <p>Latitude: {tooltip.latitude}</p>
          <p>Longitude: {tooltip.longitude}</p>
          <p>Role: {users[tooltip.userId].role}</p> */}
        </div>
      )}
    </div>
  );
}

export default withStyles(styles)(GeoLocation);
