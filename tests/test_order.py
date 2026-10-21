TIMEOUT = 5
import requests
def test_order_success(base_url, auth_headers, get_bookable):
    event = get_bookable["event"]
    categorie = get_bookable["categorie"]
    quantity = 2

    body = {
        "event_id":event['id'],
        "items":[
            {
                "category_id": categorie['id'],
                "quantity": quantity
            }
        ]
    }
    response = requests.post(f"{base_url}/api/orders",timeout=TIMEOUT, headers=auth_headers, json=body)
    assert response.status_code == 201, response.text

    order = response.json()
    assert order['event_id'] == event['id']
    assert order['status'] == "pending"
    assert order["expires_at"] is not None
    
    assert order["items"]
    assert categorie['id'] == order["items"][0]["category_id"]
    assert order["total_cents"] == categorie["price_cents"] * quantity

    retrieved_order = requests.get(f"{base_url}/api/orders/{order['id']}", headers=auth_headers, timeout=TIMEOUT)
    assert retrieved_order.status_code == 200, retrieved_order.text
    data_retrieved = retrieved_order.json()
    assert data_retrieved['id'] == order['id']
