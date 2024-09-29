from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

if __name__ == '__main__':
    # Setup transport
    transport = RequestsHTTPTransport(
        url='http://localhost:8000/graphql',
        verify=False,
        retries=3,
    )

    # Create the GraphQL client
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Define the query
    query = gql('''
        query {
            books {
                id
                title
                author
            }
        }
    ''')

    # Execute the query
    response = client.execute(query)
    print(response)
