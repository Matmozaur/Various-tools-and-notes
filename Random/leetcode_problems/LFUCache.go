package main

type LFUCache struct {
	capacity int
	minFreq  int
	dictFreq map[int]*LinkedList
	dict     map[int]*Node
}

type LinkedList struct {
	last, first *Node
	next, prev  *LinkedList
}

type LinkedListList struct {
	last, first *LinkedList
}

func (ll *LinkedList) remove(node *Node) {
	if node.prev != nil {
		node.prev.next = node.next
	} else {
		ll.first = node.next
	}
	if node.next != nil {
		node.next.prev = node.prev
	} else {
		ll.last = node.prev
	}
}

func (ll *LinkedList) addToFront(node *Node) {
	node.prev = nil
	node.next = ll.first
	if ll.first != nil {
		ll.first.prev = node
	}
	ll.first = node
	if ll.last == nil {
		ll.last = node
	}
}

type Node struct {
	next, prev *Node
	k, v, freq int
}

func ConstructorLFUCache(capacity int) LFUCache {
	return LFUCache{
		capacity: capacity,
		minFreq:  0,
		dictFreq: make(map[int]*LinkedList),
		dict:     make(map[int]*Node),
	}

}

func (this *LFUCache) Get(key int) int {
	node := this.dict[key]
	if node == nil {
		return -1
	}
	this.dictFreq[node.freq].remove(node)
	if this.dictFreq[node.freq].first == nil {
		if this.minFreq == node.freq {
			this.minFreq++
		}
	}
	node.freq++
	if this.dictFreq[node.freq] == nil {
		this.dictFreq[node.freq] = &LinkedList{}
	}
	this.dictFreq[node.freq].addToFront(node)
	return node.v
}

func (this *LFUCache) Put(key int, value int) {
	node := this.dict[key]
	if node != nil {
		_ = this.Get(key)
		node.v = value
	} else {
		if this.capacity == 0 {
			toDel := this.dictFreq[this.minFreq].last
			this.dictFreq[this.minFreq].remove(toDel)
			delete(this.dict, toDel.k)
		} else {
			this.capacity--
		}
		this.minFreq = 1
		node = &Node{
			k:    key,
			v:    value,
			freq: 1,
		}
		if this.dictFreq[1] == nil {
			this.dictFreq[1] = &LinkedList{}
		}
		this.dictFreq[1].addToFront(node)
		this.dict[key] = node
	}
}

/**
 * Your LFUCache object will be instantiated and called as such:
 * obj := Constructor(capacity);
 * param_1 := obj.Get(key);
 * obj.Put(key,value);
 */
