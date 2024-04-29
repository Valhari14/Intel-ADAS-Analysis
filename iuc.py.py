import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium.vector_layers import Circle
from sklearn.cluster import SpectralClustering

# Read the CSV data
data = pd.read_csv('cleaned_data.csv')

# Filter data for the specific alerts
alerts = ['cas_fcw', 'cas_hmw', 'cas_pcw', 'cas_ldw']

# Apply Spectral Clustering
num_clusters = 5  # You can adjust this value

# Process each alert separately
for alert in alerts:
    alert_data = data[data['Alert'] == alert]
    
    if alert_data.empty:
        continue

    # Create a Folium map centered at a specific location
    m = folium.Map(location=[alert_data['Lat'].mean(), alert_data['Long'].mean()], zoom_start=12)

    # Create a MarkerCluster layer
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each incident
    for idx, row in alert_data.iterrows():
        folium.Marker([row['Lat'], row['Long']], popup=alert).add_to(marker_cluster)

    # Apply Spectral Clustering
    spectral = SpectralClustering(n_clusters=num_clusters, random_state=0, affinity='nearest_neighbors').fit(alert_data[['Lat', 'Long']])

    # Get cluster labels
    cluster_labels = spectral.labels_

    # Group by cluster and alert
    alert_data_copy = alert_data.copy()  # Create a copy to avoid SettingWithCopyWarning
    alert_data_copy['Cluster'] = cluster_labels
    grouped = alert_data_copy.groupby(['Cluster', 'Alert'])

    # Calculate safe and danger speeds for each cluster and alert
    for (cluster, _), group in grouped:
        popup_text = f"<b>Cluster: {cluster}</b><br><br>"
        
        # Calculate safe and danger speeds
        speed_distribution = group['Speed']
        safe_speed_threshold = speed_distribution.mean()  # You can customize this based on your analysis
        danger_speed_threshold = speed_distribution.quantile(0.9)  # Adjust the quantile value as needed
        
        # Get unique time ranges in the cluster
        unique_time_ranges = group['TimeRange'].unique()
        
        # Add time range and speed info to popup
        for time_range in unique_time_ranges:
            time_range_group = group[group['TimeRange'] == time_range]
            popup_text += f"Time Range: {time_range}<br>"
            popup_text += f"Safe Speed: {safe_speed_threshold:.2f} km/h<br>"
            popup_text += f"Danger Speed: {danger_speed_threshold:.2f} km/h<br><br>"
    
        folium.Marker(
            location=[group['Lat'].mean(), group['Long'].mean()],
            popup=folium.Popup(popup_text, parse_html=True),
            icon=folium.Icon(color='black', icon='info-sign')
        ).add_to(m)
        
        # Add a circle around the blackspot
        circle_radius = 700  # Customize the radius as needed
        Circle(
            location=[group['Lat'].mean(), group['Long'].mean()],
            radius=circle_radius,
            color='black',
            fill=True,
            fill_color='grey',
            fill_opacity=0.4
        ).add_to(m)

    # Save the map to an HTML file
    m.save(f'{alert}_black_spot_map_with_radius.html')
