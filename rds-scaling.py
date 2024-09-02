import boto3

def lambda_handler(event, context):
    rds_client = boto3.client('rds')

    # Extract parameters from the event
    desired_count = event.get('detail', {}).get('desiredReplicaCount', 1)
    replica_prefix = event.get('detail', {}).get('replicaPrefix', 'replica-')
    cluster_identifier = 'your-aurora-cluster-id'  # Replace with your Aurora cluster identifier

    # Describe DB instances to find the ones belonging to the cluster
    response = rds_client.describe_db_instances()
    instances_in_cluster = [
        db_instance['DBInstanceIdentifier']
        for db_instance in response['DBInstances']
        if db_instance.get('DBClusterIdentifier') == cluster_identifier and db_instance['DBInstanceIdentifier'].startswith(replica_prefix)
    ]

    current_count = len(instances_in_cluster)
    print(f'Current replica count: {current_count}, Desired replica count: {desired_count}')

    if current_count < desired_count:
        # Scale up: Add new instances
        for i in range(current_count, desired_count):
            instance_identifier = f'{replica_prefix}{i+1:02d}'

            try:
                rds_client.create_db_instance(
                    DBInstanceIdentifier=instance_identifier,
                    DBInstanceClass='db.t3.samll',      # change your desired db instance tpye
                    Engine='aurora-mysql',  # or 'aurora-mysql', 'aurora-postgresql'
                    DBClusterIdentifier=cluster_identifier,
                    PubliclyAccessible=False
                )
                print(f'Successfully added instance {instance_identifier} to Aurora cluster {cluster_identifier}')

            except Exception as e:
                print(f'Error adding instance {instance_identifier} to Aurora cluster: {str(e)}')

    elif current_count > desired_count:
        # Scale down: Remove instances
        instances_in_cluster.sort(reverse=True)

        for i in range(current_count - desired_count):
            instance_identifier = instances_in_cluster[i]

            try:
                rds_client.delete_db_instance(
                    DBInstanceIdentifier=instance_identifier,
                    SkipFinalSnapshot=True  # Set to False if you want a final snapshot
                )
                print(f'Successfully deleted instance {instance_identifier}')

            except Exception as e:
                print(f'Error deleting instance {instance_identifier}: {str(e)}')

    return {
        'statusCode': 200,
        'body': f'Scaling operation to {desired_count} replicas completed'
    }
