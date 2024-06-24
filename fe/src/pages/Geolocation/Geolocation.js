import React, { useState, useEffect } from "react";
import { Map, Marker, ZoomControl } from "pigeon-maps";
import { withStyles } from "@material-ui/core/styles";
import useGeolocation from "./useGeolocation";

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

function GeoLocation(props) {

  // If location is allowed, fetch x,y co-ordinates returned by
  // useEffect() hook in useGeolocation.js
  const {
    data: { latitude, longitude },
  } = useGeolocation();

  // Set initial values for Latitude, Longitude, Heading, and Speed
  const [Lat, setLat] = useState(null);
  const [Lon, setLng] = useState(null);
  const [Hea, setHea] = useState(null);
  const [Spd, setSpd] = useState(null);
  
  // Define the default zoom level
  const [zoom, setZoom] = useState(18);

  // Define the default height 
  const defaultHeight = 500;

  // Define the default latitude and longitude values
  const defaultLatitude = 42.33528042187331;
  const defaultLongitude = -71.09702787206938;

  // Set the default center for the map
  const [center, setCenter] = useState([defaultLatitude, defaultLongitude]);

  // Read cookie and return the required value
  const readCookie = (name) => {

    // Each cookie has attributes separated by a ';'
    const cookies = document.cookie
      .split("; ")
      .find((row) => row.startsWith(`${name}=`));
   
    return cookies ? cookies.split("=")[1] : null;
   };

  // Report player location (and any other data)
  const reportPlayerLocation = async (userId, latitude, longitude) => {

    // Organize the data to send in a dictionary
    const requestFields = {
      'id': userId,
      'lat': latitude,
      'lon': longitude
    }

    // Attempt to send the data to the Flask server
    try {

      // Server address and port defined as env variables
      const server_address = `${process.env.REACT_APP_API_SERVICE_URL}`;

      // URL of the Flask application and the route
      const URI = server_address.concat("/location");

      // Define the necessary data, along with the player
      // data (as a JSON) to send to the Flask server. 
      const requestConfiguration = {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestFields)
      }

      // Send the player details and wait for a response 
      // (using async await)
      const response = await fetch(URI, requestConfiguration);

      // Check if response received is HTTP 200 OK
      if (response.ok) {
        console.log("Server responded!");

        // Try decoding the response data
        try{
          const responseData = await response.json();
          console.log(responseData);
        } catch (error) {
          alert("Error occured in responseData!");
          console.error(error);
        }
      }
    } catch (error) {
      alert("Error occurred in reportPlayerLocation!");
      console.error(error);
    }
    
  };

  // Function to update the location and report changes to Flask server
  const updateLocation = () => {
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
    console.log("Updating postition now...")
  };

  // UseEffect hook to update location every 10 seconds
  useEffect(() => {

    // Define the interval to update the players location
    // Since the location fetching is handled by the updateLocation()
    // call the method every 10 seconds (10 seconds = 10000 ms)
    const interval = setInterval(updateLocation, 10000);

    // Clear interval on component unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ backgroundColor: "white", padding: 72 }}>
      <button onClick={updateLocation}>Get Location</button>
      <p>Latitude: {latitude}</p>
      <p>Longitude: {longitude}</p>

      {/* These are not used but defined above */}
      {/* 'AND' these values with 'null' for now to hide them */}
      {null && Lat && <p>Latitude: {Lat}</p>}
      {null && Lon && <p>Longitude: {Lon}</p>}
      {null && Hea && <p>Heading: {Hea}</p>}
      {null && Spd && <p>Speed: {Spd}</p>}

      {/* Render the map */}
      <h1>Map</h1>
      <Map
        height={defaultHeight}
        center={center}
        defaultZoom={zoom}
        
        // Recenter the map and apply the zoom values
        onBoundsChanged={({ center, zoom }) => {
          setCenter(center);
          setZoom(zoom);
        }}
      >
        {/* Added 3 markers to represent 3 players on the map */}
        <Marker width={50} anchor={[Lat || latitude, Lon || longitude]} />
        <Marker width={50} anchor={[Lat ? Lat + 0.2 : latitude + 0.2, Lon ? Lon + 0.2 : longitude + 0.2]} />
        <Marker width={50} anchor={[Lat ? Lat - 0.2 : latitude - 0.2, Lon ? Lon - 0.2 : longitude - 0.2]} />

        {/* Add default +/- buttons to allow zoom controls on the map */}
        <ZoomControl />
      </Map>
    </div>
  );
}

export default withStyles(styles)(GeoLocation);
